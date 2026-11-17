#!/usr/bin/env python3
"""Build docs/feed.json (format version 1) for the app from products.csv + prices.csv.

products.csv: id,name,category,unit,aliases,image   (image = file name in docs/images/ or full https URL)
prices.csv  : product_id,amount,amount_high,place,observed_on,note   (amount_high optional; DA ranges)
"""
import argparse, csv, json, sys
from datetime import datetime, timezone, timedelta

UNITS = {"kg", "piece", "liter", "pack", "bundle"}
TYPES = {"DA_REFERENCE", "PSA_STATISTICS", "COMMUNITY_REPORTED", "STORE_REPORTED"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", default="data/products.csv"); ap.add_argument("--prices", default="data/prices.csv")
    ap.add_argument("--source-name", required=True); ap.add_argument("--report-period", required=True)
    ap.add_argument("--attribution", default=""); ap.add_argument("--source-url", default="")
    ap.add_argument("--type", default="DA_REFERENCE", choices=sorted(TYPES))
    ap.add_argument("--image-base", default="", help="https URL of docs/images/, e.g. https://USER.github.io/REPO/images/")
    ap.add_argument("--out", default="docs/feed.json")
    a = ap.parse_args()

    errors, products = [], []
    with open(a.products, newline="", encoding="utf-8") as f:
        for n, r in enumerate(csv.DictReader(f), start=2):
            if r["unit"] not in UNITS: errors.append(f"products line {n}: bad unit {r['unit']!r}"); continue
            img = (r.get("image") or "").strip()
            if img and not img.startswith("https://"): img = a.image_base.rstrip("/") + "/" + img if a.image_base else ""
            p = {"id": int(r["id"]), "name": r["name"].strip(), "category": r["category"].strip(),
                 "unit": r["unit"], "aliases": (r.get("aliases") or "").strip()}
            if img: p["image_url"] = img
            products.append(p)
    units = {p["id"]: p["unit"] for p in products}

    prices = []
    with open(a.prices, newline="", encoding="utf-8") as f:
        for n, r in enumerate(csv.DictReader(f), start=2):
            try:
                pid, amount = int(r["product_id"]), float(r["amount"])
                high = float(r["amount_high"]) if (r.get("amount_high") or "").strip() else None
                datetime.strptime(r["observed_on"], "%Y-%m-%d")
            except Exception:
                errors.append(f"prices line {n}: bad number/date"); continue
            if pid not in units: errors.append(f"prices line {n}: unknown product_id {pid}"); continue
            if amount <= 0 or (high is not None and high < amount): errors.append(f"prices line {n}: bad amount/range"); continue
            row = {"product_id": pid, "amount": round(amount, 2), "unit": units[pid], "place": r["place"].strip(), "observed_on": r["observed_on"]}
            if high is not None and high != amount: row["amount_high"] = round(high, 2)
            if (r.get("note") or "").strip(): row["note"] = r["note"].strip()
            prices.append(row)
    if errors: print("Fix these first:\n  " + "\n  ".join(errors), file=sys.stderr); sys.exit(1)
    if not prices: sys.exit("No prices to publish.")

    manila = timezone(timedelta(hours=8))
    feed = {"version": 1, "generated_at": datetime.now(manila).isoformat(timespec="seconds"),
            "source": {"name": a.source_name, "type": a.type, "report_period": a.report_period,
                       "attribution": a.attribution, "url": a.source_url},
            "products": products, "prices": prices}
    with open(a.out, "w", encoding="utf-8") as f: json.dump(feed, f, ensure_ascii=False, indent=1)
    print(f"Wrote {a.out}: {len(products)} products, {len(prices)} prices")

if __name__ == "__main__":
    main()
