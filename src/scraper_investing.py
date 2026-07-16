"""
scraper_investing.py
=====================
Scraper berita Investing.com (Indonesia). Sama seperti scraper_cnbc.py,
default-nya menghasilkan dataset dummy realistis (offline & reproducible)
supaya pipeline langsung jalan untuk sidang KTI.

Bagian `_scrape_live()` menyediakan referensi implementasi requests +
BeautifulSoup; Investing.com kerap menolak request non-browser sehingga
untuk scraping riil kemungkinan perlu Selenium.

Output: CSV per periode di `data/raw_news/investing_<periode>.csv`
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


def _scrape_live(kategori: str = "politics", max_pages: int = 3) -> pd.DataFrame:
    """Best-effort scraper Investing.com Indonesia."""
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "id-ID,id;q=0.9"})
    rows = []
    for page in range(1, max_pages + 1):
        url = f"https://id.investing.com/news/{kategori}/{page}"
        try:
            resp = session.get(url, timeout=15)
        except requests.RequestException as e:
            print(f"[investing-live] gagal: {e}")
            break
        if resp.status_code != 200:
            print(f"[investing-live] status {resp.status_code} di page {page}")
            break
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("article a.title, a.news-link")
        if not articles:
            break
        for a in articles:
            judul = a.get_text(strip=True)
            href = a.get("href", "")
            if not judul or not href:
                continue
            rows.append({
                "tanggal": pd.Timestamp.today().strftime("%Y-%m-%d"),
                "sumber": "Investing",
                "judul": judul,
                "url": href if href.startswith("http") else f"https://id.investing.com{href}",
            })
        time.sleep(2.0)
    return pd.DataFrame(rows)


def scrape_periode(periode_key: str, berita_per_periode: int = 60) -> pd.DataFrame:
    return generate_dummy(
        sumber="Investing",
        periode_key=periode_key,
        berita_per_periode=berita_per_periode,
        seed=99,  # seed beda supaya distribusi tanggal berbeda dengan CNBC
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dummy", "live"], default="dummy")
    parser.add_argument("--per-periode", type=int, default=60)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "live":
        df = _scrape_live()
        out = OUT_DIR / "investing_live.csv"
        df.to_csv(out, index=False)
        print(f"[investing-live] {len(df)} berita -> {out}")
        return

    total = 0
    for key, info in PERIODE.items():
        df = scrape_periode(key, args.per_periode)
        out = OUT_DIR / f"investing_{info['label']}.csv"
        df.to_csv(out, index=False)
        print(f"[investing] {info['label']}: {len(df)} berita -> {out.name}")
        total += len(df)
    print(f"[investing] total: {total} berita")


if __name__ == "__main__":
    main()
