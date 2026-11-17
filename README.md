# presyo-feed-repo (free feed + image hosting for PresyoAlert PH)

GitHub Pages hosts `docs/feed.json` and `docs/images/`. A free GitHub Actions job runs daily, downloads the newest
DA price-monitoring PDF, reads the per-market table, and rewrites `docs/feed.json`. If any step fails, the old feed
stays online (the app keeps showing the last good data).

## Setup (once, all free)
1. Create a public GitHub repo (e.g. `presyo-feed`) and upload everything in this folder.
2. Settings -> Pages -> Deploy from branch -> `main` / `/docs`.
3. Edit `data/products.csv` (your 15-30 products; ids must stay stable) and `data/name_map.csv`
   (DA column header -> product id). Run once: Actions tab -> "Update price feed" -> Run workflow.
4. Your feed URL: `https://YOURNAME.github.io/presyo-feed/feed.json`. Put it in `FEED_URL` in the Android app.

## Images (shown in the app)
Put small files (about 400 px, JPG/WebP, under 60 KB) in `docs/images/` and write the file name in the `image` column
of `products.csv`. Use only photos you took or that are public-domain/CC0. Do not copy DA report photos
("credits to the owner") or pictures from stores/other sites.

## Run on your PC instead (needs Python 3)
    pip install pdfplumber
    python scripts/da_pdf_to_csv.py my_report.pdf --debug
    python scripts/csv_to_feed.py --source-name "DA Daily Price Monitoring" --report-period "$(cat data/report_date.txt)" --out docs/feed.json
(PowerShell: use `(Get-Content data\report_date.txt)` for the period.)

## Honest limits
- The PDF reader is tested only on a synthetic table that copies the DA layout. Send a real PDF if `--debug` shows wrong headers.
- `fetch_latest_da.py` assumes the DA page links files named `Price-Monitoring-<Month>-<D>-<YYYY>.pdf`; the DA site may block
  or change. Check the DA site terms and keep attribution.
- The daily national report covers Metro Manila markets. For other regions use that regional DA office's PDF
  (pass the PDF to `da_pdf_to_csv.py`; the table layout may differ).
- PSA OpenSTAT is not wired in yet: export a table as CSV, convert it to `prices.csv`, and build with `--type PSA_STATISTICS`.
