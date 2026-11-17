#!/usr/bin/env python3
"""Download the newest 'Price-Monitoring-<Month>-<D>-<YYYY>.pdf' linked from the DA price monitoring page."""
import argparse, re, sys, urllib.request
from datetime import datetime
from urllib.parse import urljoin

PAGE = "https://www.da.gov.ph/price-monitoring/"
UA = {"User-Agent": "PresyoAlertFeedBot/1.0 (+personal non-commercial price tracker)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="data/latest.pdf"); ap.add_argument("--page", default=PAGE)
    a = ap.parse_args()
    html = get(a.page).decode("utf-8", "ignore")
    best = None
    for href in re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, flags=re.I):
        m = re.search(r"Price-Monitoring-([A-Za-z]+)-(\d{1,2})-(\d{4})", href)
        if not m: continue
        try: d = datetime.strptime(" ".join(m.groups()), "%B %d %Y")
        except ValueError: continue
        if best is None or d > best[0]: best = (d, urljoin(a.page, href))
    if not best: sys.exit("No Price-Monitoring PDF link found; the DA page layout may have changed.")
    print("Newest report:", best[0].date(), best[1])
    with open(a.out, "wb") as f: f.write(get(best[1]))

if __name__ == "__main__":
    main()
