#!/usr/bin/env python3
"""Read the DA 'DAILY PRICE INDEX' (NCR) PDF into data/prices.csv. Free: pdfplumber only.

The PDF is a 3-column table (COMMODITY | SPECIFICATION | PREVAILING RETAIL PRICE), with section rows
(e.g. 'LOCAL COMMERCIAL RICE', 'EGG'). One prevailing (average) price per commodity for selected NCR wet markets.
data/name_map.csv maps (section, name-prefix, optional spec text) -> product id. Rows with 'n/a' are skipped.
"""
import argparse, csv, re, sys
from datetime import datetime
import pdfplumber

DATE_RE = re.compile(r"\(?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\)?")
PRICE_RE = re.compile(r"^\d[\d,]*\.\d{1,2}$")

def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\n", " ")).strip()

def load_map(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [(r["section"].strip().lower(), r["match"].strip().lower(), r["spec_contains"].strip().lower(), int(r["product_id"]))
                for r in csv.DictReader(f)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--map", default="data/name_map.csv")
    ap.add_argument("--out", default="data/prices.csv"); ap.add_argument("--date-out", default="data/report_date.txt")
    ap.add_argument("--place", default="NCR wet markets (average)")
    ap.add_argument("--note", default="DA Daily Price Index, NCR: prevailing retail price (average of selected wet markets)")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    mapping = load_map(a.map)

    report_date, section, items = None, "", []
    with pdfplumber.open(a.pdf) as pdf:
        for page in pdf.pages:
            if report_date is None:
                m = DATE_RE.search(page.extract_text() or "")
                if m:
                    try: report_date = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date()
                    except ValueError: pass
            for t in page.extract_tables() or []:
                for r in t:
                    if not r or len(r) < 3: continue
                    name, spec, price = clean(r[0]), clean(r[1]), clean(r[2])
                    if not name or name.upper() == "COMMODITY": continue
                    if not spec and not price:               # section row
                        section = name.lower(); continue
                    items.append((section, name, spec, price))
    if report_date is None:
        sys.exit("Could not find the report date (e.g. '(Wednesday, November 18, 2026)').")
    if a.debug: print(f"{len(items)} table rows; date {report_date}", file=sys.stderr)

    out, used = [], set()
    for sec, name, spec, price in items:
        low = name.lower()
        for i, (msec, mname, mspec, pid) in enumerate(mapping):
            if sec == msec and low.startswith(mname) and mspec in spec.lower():
                if i in used: break                          # first match wins
                used.add(i)
                if PRICE_RE.match(price):
                    out.append((pid, float(price.replace(",", "")), name, spec))
                elif a.debug: print(f"  skip {name!r}: price {price!r}", file=sys.stderr)
                break
    missing = [mapping[i][1] for i in range(len(mapping)) if i not in used]
    if not out: sys.exit("No mapped prices found. Run with --debug; the PDF layout or name_map.csv may need an update.")
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["product_id", "amount", "amount_high", "place", "observed_on", "note"])
        for pid, amt, name, spec in out:
            w.writerow([pid, f"{amt:.2f}", "", a.place, report_date.isoformat(), f"{a.note}; {name}" + (f" ({spec})" if spec else "")])
    with open(a.date_out, "w") as f: f.write(report_date.strftime("%d %b %Y"))
    print(f"{len(out)} prices for {report_date}")
    if missing: print("Not found or n/a today:", ", ".join(missing))

if __name__ == "__main__":
    main()
