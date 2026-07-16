"""
scraper_cnbc.py
================
Scraper berita CNBC Indonesia. Karena arsip lampau (2022, 2023-2024, 2025)
sering kali diblokir / berubah struktur DOM-nya, script ini memakai dataset
dummy realistis yang di-bundle di `_dummy_dataset.py` sebagai sumber
utama untuk reproducibility sidang KTI.

Bagian `_scrape_live()` DISERTAKAN sebagai referensi kalau Anda ingin
menjalankan scraping riil di kemudian hari (memerlukan akses internet
dan mungkin `Selenium` bila situs mem-blokir requests biasa).

Output: CSV per periode di `data/raw_news/cnbc_<periode>.csv`
Kolom : tanggal, sumber, judul, url
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from _dummy_dataset import PERIODE, generate_dummy

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "data" / "raw_news"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36")


# ---------------------------------------------------------------------------
# Live scraper (opsional). Dipanggil bila --mode=live.
# ---------------------------------------------------------------------------
def _scrape_live(query: str = "geopolitik",
                 max_pages: int = 3) -> pd.DataFrame:
    """Scrape indeks pencarian CNBC Indonesia. Best-effort saja."""
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    rows = []
    for page in range(1, max_pages + 1):
        url = f"https://www.cnbcindonesia.com/search?query={query}&p={page}"
        try:
            resp = session.get(url, timeout=15)
        except requests.RequestException as e:
            print(f"[cnbc-live] gagal: {e}")
            break
        if resp.status_code != 200:
            print(f"[cnbc-live] status {resp.status_code} di page {page}")
            break
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("article a[href*='/news/']")
        if not articles:
            break
        for a in articles:
            judul = a.get_text(strip=True)
            href = a.get("href", "")
            if not judul or not href:
                continue
            rows.append({
                "tanggal": pd.Timestamp.today().strftime("%Y-%m-%d"),
                "sumber": "CNBC",
                "judul": judul,
                "url": href,
            })
        time.sleep(1.5)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dummy scraper (default). Reproducible & offline-ready.
# ---------------------------------------------------------------------------
def scrape_periode(periode_key: str, berita_per_periode: int = 60) -> pd.DataFrame:
    return generate_dummy(
        sumber="CNBC",
        periode_key=periode_key,
        berita_per_periode=berita_per_periode,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dummy", "live"], default="dummy")
    parser.add_argument("--per-periode", type=int, default=60)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "live":
        df = _scrape_live()
        out = OUT_DIR / "cnbc_live.csv"
        df.to_csv(out, index=False)
        print(f"[cnbc-live] {len(df)} berita -> {out}")
        return

    total = 0
    for key, info in PERIODE.items():
        df = scrape_periode(key, args.per_periode)
        out = OUT_DIR / f"cnbc_{info['label']}.csv"
        df.to_csv(out, index=False)
        print(f"[cnbc] {info['label']}: {len(df)} berita -> {out.name}")
        total += len(df)
    print(f"[cnbc] total: {total} berita")


if __name__ == "__main__":
    main()
