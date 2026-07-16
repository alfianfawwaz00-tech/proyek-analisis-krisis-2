"""
stock_fetch.py
==============
Ambil harga saham siklikal Indonesia dari Yahoo Finance untuk 3 periode:
1) Feb - Des 2022    (Krisis energi Rusia-Ukraina)
2) Okt 2023 - Jun 2024 (Konflik Timur Tengah + suku bunga tinggi)
3) Jan - Des 2025    (Perang tarif & ketegangan geopolitik)

Menghitung `pct_change` harian per ticker.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent

TICKERS = ["ADRO.JK", "ENRG.JK", "ITMG.JK", "BBCA.JK"]

PERIODE = {
    "P1_2022_RusiaUkraina": ("2022-02-01", "2022-12-31"),
    "P2_2023_2024_TimurTengah": ("2023-10-01", "2024-06-30"),
    "P3_2025_PerangTarif": ("2025-01-01", "2025-12-31"),
}


def fetch_ticker(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Unduh harga OHLCV harian + pct_change."""
    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
    )
    if df.empty:
        return pd.DataFrame()

    # yfinance kadang mengembalikan MultiIndex kolom -> ratakan
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["tanggal"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df["ticker"] = ticker
    df["pct_change"] = df["Close"].pct_change() * 100
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    return df[["tanggal", "ticker", "open", "high", "low",
               "close", "volume", "pct_change"]]


def fetch_semua() -> pd.DataFrame:
    """Loop semua ticker × semua periode, return satu DataFrame gabungan."""
    frames: list[pd.DataFrame] = []
    for label, (start, end) in PERIODE.items():
        for t in TICKERS:
            print(f"[fetch] {t}  {start} .. {end}  ({label})")
            df = fetch_ticker(t, start, end)
            if df.empty:
                print(f"        ! tidak ada data untuk {t} {label}")
                continue
            df["periode"] = label
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    out_dir = BASE_DIR / "data" / "raw_news"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = fetch_semua()
    out_csv = BASE_DIR / "data" / "stock_prices.csv"
    df.to_csv(out_csv, index=False)
    print(f"Tersimpan: {out_csv}  ({len(df)} baris)")
