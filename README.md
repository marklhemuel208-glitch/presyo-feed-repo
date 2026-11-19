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

## Price history (trend chart in the app)
The daily job now appends each day's prices to `data/history.csv` (last 45 days) and publishes them all in `feed.json`.
To load earlier days right away, run **Actions -> Backfill price history (manual) -> Run workflow** (default: 21 newest DA reports;
reports the reader cannot understand are skipped).

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
- The reader is tested on the real DA Daily Price Index PDF of 18 Nov 2026 (all 15 mapped products matched the report). If the DA changes the layout, the Actions run fails and the old feed stays online.
- The Daily Price Index gives ONE prevailing (average) price per commodity for selected NCR wet markets, not a price per market or per store. The app labels it as a government reference, not a live stall price.
- `docs/privacy.md` is a draft privacy policy served at `/privacy.html`; put your contact email in it.
- `da_market_table_to_csv.py` is the older per-market range reader, kept for regional DA files (untested on real regional PDFs).
- To track other products, add them to `data/products.csv` and a line to `data/name_map.csv` (section, start of the commodity name, optional specification text).
- Check DA site terms and keep the attribution. PSA OpenSTAT is not wired in yet.
