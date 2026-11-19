#!/usr/bin/env python3
"""Merge one day's prices CSV into data/history.csv (keeps the last N days). Free, no dependencies.

    python scripts/update_history.py data/prices.csv
    python scripts/update_history.py --print-latest        # prints the newest date in history, e.g. 18 Nov 2026
"""
import argparse, csv, os, sys
from datetime import date, timedelta

FIELDS = ["product_id", "amount", "amount_high", "place", "observed_on", "note"]

def read(path):
    if not os.path.exists(path): return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new_csv", nargs="?"); ap.add_argument("--history", default="data/history.csv")
    ap.add_argument("--keep-days", type=int, default=45); ap.add_argument("--print-latest", action="store_true")
    a = ap.parse_args()
    rows = {}
    for r in read(a.history):
        rows[(r["observed_on"], r["product_id"], r["place"])] = {k: r.get(k, "") for k in FIELDS}
    if a.print_latest:
        if not rows: sys.exit("history is empty")
        print(date.fromisoformat(max(k[0] for k in rows)).strftime("%d %b %Y")); return
    if not a.new_csv: sys.exit("give the new prices CSV")
    added = 0
    for r in read(a.new_csv):
        key = (r["observed_on"], r["product_id"], r["place"])
        added += key not in rows
        rows[key] = {k: r.get(k, "") for k in FIELDS}          # newest data for the same day wins
    if not rows: sys.exit("nothing to write")
    latest = date.fromisoformat(max(k[0] for k in rows))
    cutoff = (latest - timedelta(days=a.keep_days)).isoformat()
    kept = sorted((v for k, v in rows.items() if k[0] >= cutoff), key=lambda v: (v["observed_on"], int(v["product_id"])))
    os.makedirs(os.path.dirname(a.history) or ".", exist_ok=True)
    with open(a.history, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(kept)
    days = len({v["observed_on"] for v in kept})
    print(f"history: {len(kept)} rows over {days} day(s), {added} new, latest {latest}")

if __name__ == "__main__":
    main()
