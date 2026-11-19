#!/usr/bin/env python3
"""Download DA Daily Price Index PDFs listed on https://www.da.gov.ph/price-monitoring/

Default: newest one -> --out.   With --limit N --out-dir DIR: the newest N (one per date) -> DIR.
File names vary ('Daily-Price-Index-<Month>-<D>-<YYYY>.pdf', '<Month>-<D>-<YYYY>-DPI-AFC.pdf', 'Revised-...');
one row on the page has a doubled URL, so we keep the last 'https://' part.
"""
import argparse, os, re, sys, time, urllib.request
from datetime import datetime
from urllib.parse import urljoin

PAGE = "https://www.da.gov.ph/price-monitoring/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; PresyoAlertFeedBot/1.0; personal non-commercial price tracker)"}

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:
            if i == tries - 1: raise
            print(f"retry {i + 1} after error: {e}", file=sys.stderr); time.sleep(5 * (i + 1))

def candidates(html, page):
    best = {}                                    # date -> (revised, url)
    for href in re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, flags=re.I):
        if href.count("https://") > 1: href = href[href.rfind("https://"):]
        fn = href.rsplit("/", 1)[-1]
        if not re.search(r"Daily-Price-Index|DPI", fn, re.I) or re.search(r"Weekly", fn, re.I): continue
        m = re.search(r"([A-Za-z]+)-(\d{1,2})-(\d{4})", fn)
        if not m: continue
        try: d = datetime.strptime(" ".join(m.groups()), "%B %d %Y").date()
        except ValueError: continue
        rev = "revised" in fn.lower()
        if d not in best or (rev and not best[d][0]): best[d] = (rev, urljoin(page, href))
    return sorted(((d, v[1]) for d, v in best.items()), reverse=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/latest.pdf"); ap.add_argument("--page", default=PAGE)
    ap.add_argument("--limit", type=int, default=1); ap.add_argument("--out-dir")
    a = ap.parse_args()
    found = candidates(get(a.page).decode("utf-8", "ignore"), a.page)
    if not found: sys.exit("No Daily Price Index PDF link found; the DA page layout may have changed.")
    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)
        for d, url in found[:a.limit]:
            path = os.path.join(a.out_dir, f"{d.isoformat()}.pdf")
            try:
                data = get(url)
            except Exception as e:
                print(f"skip {d}: {e}", file=sys.stderr); continue
            with open(path, "wb") as f: f.write(data)
            print("saved", path)
    else:
        d, url = found[0]
        print("Newest report:", d, url)
        with open(a.out, "wb") as f: f.write(get(url))

if __name__ == "__main__":
    main()
