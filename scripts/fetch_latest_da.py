#!/usr/bin/env python3
"""Download the newest DA Daily Price Index PDF listed on https://www.da.gov.ph/price-monitoring/

File names vary: 'Daily-Price-Index-<Month>-<D>-<YYYY>.pdf', '<Month>-<D>-<YYYY>-DPI-AFC.pdf', 'Revised-...'.
One row on the page has a doubled URL; we keep the last 'https://' part.
"""
import argparse, re, sys, urllib.request
from datetime import datetime
from urllib.parse import urljoin

PAGE = "https://www.da.gov.ph/price-monitoring/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; PresyoAlertFeedBot/1.0; personal non-commercial price tracker)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="data/latest.pdf"); ap.add_argument("--page", default=PAGE)
    a = ap.parse_args()
    html = get(a.page).decode("utf-8", "ignore")
    best = None
    for href in re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, flags=re.I):
        if href.count("https://") > 1: href = href[href.rfind("https://"):]
        fn = href.rsplit("/", 1)[-1]
        if not re.search(r"Daily-Price-Index|DPI", fn, re.I) or re.search(r"Weekly", fn, re.I): continue
        m = re.search(r"([A-Za-z]+)-(\d{1,2})-(\d{4})", fn)
        if not m: continue
        try: d = datetime.strptime(" ".join(m.groups()), "%B %d %Y")
        except ValueError: continue
        key = (d, "revised" in fn.lower())
        if best is None or key > best[0]: best = (key, urljoin(a.page, href))
    if not best: sys.exit("No Daily Price Index PDF link found; the DA page layout may have changed.")
    print("Newest report:", best[0][0].date(), best[1])
    with open(a.out, "wb") as f: f.write(get(best[1]))

if __name__ == "__main__":
    main()
