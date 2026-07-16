"""
run_pipeline.py
================
Orkestrator ujung-ke-ujung:

  1. scraper_cnbc      -> data/raw_news/cnbc_*.csv
  2. scraper_investing -> data/raw_news/investing_*.csv
  3. load_to_sql       -> database.db  (news_sentiment + stock_prices)
  4. join_export       -> data/output/hasil_gabungan.xlsx

Jalankan:
    python run_pipeline.py                 # dummy dataset (default)
    python run_pipeline.py --per-periode 80

Untuk mencoba scraping riil (best-effort):
    python src/scraper_cnbc.py       --mode live
    python src/scraper_investing.py  --mode live
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


def run(cmd: list[str]) -> None:
    print("\n$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=SRC)
    if r.returncode != 0:
        sys.exit(f"Gagal menjalankan: {' '.join(cmd)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-periode", type=int, default=60,
                        help="jumlah berita dummy per (sumber, periode)")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="lewati langkah scraping (pakai CSV yang sudah ada)")
    parser.add_argument("--skip-stock", action="store_true",
                        help="lewati unduh harga (butuh internet)")
    args = parser.parse_args()

    py = sys.executable

    if not args.skip_scrape:
        run([py, "scraper_cnbc.py", "--per-periode", str(args.per_periode)])
        run([py, "scraper_investing.py", "--per-periode", str(args.per_periode)])

    if args.skip_stock:
        # Muat berita saja
        run([py, "-c",
             "import sqlite3, load_to_sql as L; "
             "L.DB_PATH.unlink(missing_ok=True); "
             "c=sqlite3.connect(L.DB_PATH); L.init_schema(c); "
             "print('berita:', L.load_news(c)); c.close()"])
    else:
        run([py, "load_to_sql.py"])

    run([py, "join_export.py"])

    print("\nSelesai. Cek:")
    print(f"  - {ROOT/'database.db'}")
    print(f"  - {ROOT/'data'/'output'/'hasil_gabungan.xlsx'}")


if __name__ == "__main__":
    main()
