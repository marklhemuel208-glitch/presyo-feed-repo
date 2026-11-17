#!/usr/bin/env python3
"""Read a DA 'Retail Price Range ... per Market' PDF into prices.csv (free: pdfplumber).

Reads table CELLS by position (not text order), so blank / NOT AVAILABLE cells cannot shift prices
onto the wrong product. Prices are kept as low-high ranges. Unmapped columns are listed so you can
add them to data/name_map.csv. Use --debug to see what was detected.
"""
import argparse, csv, re, sys
from datetime import datetime
import pdfplumber

DATE_RE = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})")
NUM = r"(\d[\d,]*(?:\.\d+)?)"
RANGE_RE = re.compile(rf"^{NUM}\*{{0,3}}\s*-\s*{NUM}\*{{0,3}}$")
SINGLE_RE = re.compile(rf"^{NUM}\*{{0,3}}$")

def norm(s):
    s = (s or "").replace("\n", " ")
    s = re.sub(r"[\*\u1d43-\u1d48]", "", s)          # footnote marks
    return re.sub(r"\s+", " ", s).strip().lower()

def parse_cell(text):
    t = re.sub(r"[^\d.,\-\* ]", "", (text or "").replace("\n", " ")).strip()
    if not t: return None
    m = RANGE_RE.match(t)
    if m: return float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
    m = SINGLE_RE.match(t)
    if m:
        v = float(m.group(1).replace(",", "")); return v, v
    return None

def load_map(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = [(r["da_header"].strip().lower(), int(r["product_id"])) for r in csv.DictReader(f)]
    return sorted(rows, key=lambda x: -len(x[0]))     # longest match first

def map_header(h, mapping):
    for key, pid in mapping:
        if key in h: return pid
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--map", default="data/name_map.csv")
    ap.add_argument("--out", default="data/prices.csv"); ap.add_argument("--date-out", default="data/report_date.txt")
    ap.add_argument("--note", default="DA daily price monitoring, per-market table")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    mapping = load_map(a.map)

    report_date, rows, unmapped, skipped = None, [], set(), 0
    with pdfplumber.open(a.pdf) as pdf:
        for page in pdf.pages:
            if report_date is None:
                m = DATE_RE.search(page.extract_text() or "")
                if m:
                    try: report_date = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date()
                    except ValueError: pass
            tables = page.extract_tables() or []
            if not any(t and t[0] and "market" in norm(t[0][0]) for t in tables):
                tables = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"}) or []
            for t in tables:
                hi = next((i for i, r in enumerate(t) if r and "market" in norm(r[0])), None)
                if hi is None: continue
                headers = [norm(c) for c in t[hi]]
                pids = [map_header(h, mapping) if i > 0 else None for i, h in enumerate(headers)]
                if a.debug: print("HEADERS:", headers, "->", pids, file=sys.stderr)
                for i, h in enumerate(headers):
                    if i > 0 and h and pids[i] is None: unmapped.add(h)
                for r in t[hi + 1:]:
                    market = re.sub(r"\s+", " ", (r[0] or "").replace("\n", " ")).strip()
                    if not market or "source" in market.lower(): continue
                    for i, cell in enumerate(r):
                        if i == 0 or i >= len(pids) or pids[i] is None: continue
                        v = parse_cell(cell)
                        if v is None: continue
                        lo, hi_ = v
                        if lo <= 0 or hi_ < lo: skipped += 1; continue
                        rows.append((pids[i], lo, hi_ if hi_ != lo else "", market))
    if report_date is None:
        sys.exit("Could not find the report date (e.g. 'Wednesday, January 15, 2025') in the PDF.")
    if not rows:
        sys.exit("No prices found. Run with --debug and send me the output / the PDF.")
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["product_id", "amount", "amount_high", "place", "observed_on", "note"])
        for pid, lo, hi_, market in rows:
            w.writerow([pid, f"{lo:.2f}", f"{hi_:.2f}" if hi_ != "" else "", market, report_date.isoformat(), a.note])
    with open(a.date_out, "w") as f: f.write(report_date.strftime("%d %b %Y"))
    print(f"{len(rows)} prices for {report_date}; skipped {skipped} bad cells")
    if unmapped: print("Unmapped DA columns (add to name_map.csv if you want them):\n  " + "\n  ".join(sorted(unmapped)))

if __name__ == "__main__":
    main()
