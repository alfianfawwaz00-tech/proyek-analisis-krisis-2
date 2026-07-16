"""
load_to_sql.py
==============
Muat data berita (sudah di-skor) dan harga saham ke SQLite (`database.db`).

Tabel:
- news_sentiment(id, tanggal, sumber, judul, url,
                 skor_positif, skor_negatif, skor_net)
- stock_prices  (id, tanggal, ticker, open, high, low, close, volume,
                 pct_change, periode)

View:
- daily_sentiment(tanggal, total_positif, total_negatif,
                  skor_net_harian, jumlah_berita)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from sentiment import skor_dataframe
from stock_fetch import fetch_semua

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"
RAW_DIR = BASE_DIR / "data" / "raw_news"


SCHEMA_SQL = """
DROP VIEW  IF EXISTS daily_sentiment;
DROP TABLE IF EXISTS news_sentiment;
DROP TABLE IF EXISTS stock_prices;

CREATE TABLE news_sentiment (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal       TEXT    NOT NULL,
    sumber        TEXT    NOT NULL,
    judul         TEXT    NOT NULL,
    url           TEXT,
    skor_positif  INTEGER NOT NULL DEFAULT 0,
    skor_negatif  INTEGER NOT NULL DEFAULT 0,
    skor_net      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_news_tanggal ON news_sentiment(tanggal);

CREATE TABLE stock_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal     TEXT    NOT NULL,
    ticker      TEXT    NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    pct_change  REAL,
    periode     TEXT
);
CREATE INDEX idx_stock_tanggal_ticker ON stock_prices(tanggal, ticker);

CREATE VIEW daily_sentiment AS
SELECT
    tanggal,
    SUM(skor_positif) AS total_positif,
    SUM(skor_negatif) AS total_negatif,
    SUM(skor_net)     AS skor_net_harian,
    COUNT(*)          AS jumlah_berita
FROM news_sentiment
GROUP BY tanggal;
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def load_news(conn: sqlite3.Connection) -> int:
    csvs = sorted(RAW_DIR.glob("*.csv"))
    if not csvs:
        raise SystemExit(
            "Tidak ada CSV di data/raw_news. Jalankan scraper terlebih dahulu."
        )
    df_all = pd.concat([pd.read_csv(p) for p in csvs], ignore_index=True)
    df_skor = skor_dataframe(df_all)
    df_skor.to_sql("news_sentiment", conn, if_exists="append", index=False)
    conn.commit()
    return len(df_skor)


def load_stocks(conn: sqlite3.Connection) -> int:
    print("[stock] mengunduh harga dari Yahoo Finance ...")
    df = fetch_semua()
    if df.empty:
        print("[stock] PERINGATAN: yfinance tidak mengembalikan data.")
        return 0
    df.to_sql("stock_prices", conn, if_exists="append", index=False)
    conn.commit()
    return len(df)


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        init_schema(conn)
        n_news = load_news(conn)
        n_stock = load_stocks(conn)
        print(f"[db] {n_news} berita & {n_stock} baris harga saham dimuat.")
        print(f"[db] file: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
