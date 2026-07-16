"""
join_export.py
==============
JOIN antara `daily_sentiment` dan `stock_prices` di SQLite,
lalu ekspor ke Excel multi-sheet.

Dua varian JOIN:
- Same-day : sentimen tanggal T   <->  harga tanggal T
- Lag H+1  : sentimen tanggal T   <->  harga tanggal T+1
             (pakai DATE(daily_sentiment.tanggal, '+1 day'))

Sheet Excel yang dihasilkan:
- ringkasan_korelasi      -> Pearson & Spearman per (periode, ticker, mode)
- daily_sentiment         -> tabel agregasi harian
- <periode>_<ticker>_H0   -> same-day
- <periode>_<ticker>_H1   -> lag H+1

Output: data/output/hasil_gabungan.xlsx
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"
OUT_XLSX = BASE_DIR / "data" / "output" / "hasil_gabungan.xlsx"

TICKERS = ["ADRO.JK", "ENRG.JK", "ITMG.JK", "BBCA.JK"]

PERIODE = {
    "P1_2022_RusiaUkraina": ("2022-02-01", "2022-12-31"),
    "P2_2023_2024_TimurTengah": ("2023-10-01", "2024-06-30"),
    "P3_2025_PerangTarif": ("2025-01-01", "2025-12-31"),
}

SQL_SAMEDAY = """
SELECT
    ds.tanggal              AS tanggal,
    ds.total_positif        AS total_positif,
    ds.total_negatif        AS total_negatif,
    ds.skor_net_harian      AS skor_net_harian,
    ds.jumlah_berita        AS jumlah_berita,
    sp.ticker               AS ticker,
    sp.open, sp.high, sp.low, sp.close, sp.volume,
    sp.pct_change           AS pct_change
FROM daily_sentiment ds
LEFT JOIN stock_prices sp
       ON sp.tanggal = ds.tanggal
      AND sp.ticker  = ?
WHERE ds.tanggal BETWEEN ? AND ?
ORDER BY ds.tanggal;
"""

SQL_LAG_H1 = """
SELECT
    ds.tanggal              AS tanggal_berita,
    sp.tanggal              AS tanggal_harga,
    ds.total_positif        AS total_positif,
    ds.total_negatif        AS total_negatif,
    ds.skor_net_harian      AS skor_net_harian,
    ds.jumlah_berita        AS jumlah_berita,
    sp.ticker               AS ticker,
    sp.open, sp.high, sp.low, sp.close, sp.volume,
    sp.pct_change           AS pct_change
FROM daily_sentiment ds
LEFT JOIN stock_prices sp
       ON sp.tanggal = DATE(ds.tanggal, '+1 day')
      AND sp.ticker  = ?
WHERE ds.tanggal BETWEEN ? AND ?
ORDER BY ds.tanggal;
"""


def _safe_corr(x: pd.Series, y: pd.Series) -> tuple[float, float, float, float, int]:
    """Return (pearson_r, pearson_p, spearman_r, spearman_p, n)."""
    mask = x.notna() & y.notna()
    n = int(mask.sum())
    if n < 3 or x[mask].nunique() < 2 or y[mask].nunique() < 2:
        return (np.nan, np.nan, np.nan, np.nan, n)
    pr, pp = pearsonr(x[mask], y[mask])
    sr, sp = spearmanr(x[mask], y[mask])
    return (pr, pp, sr, sp, n)


def _sanitize_sheet(name: str) -> str:
    # Excel batasi 31 char & tidak boleh karakter tertentu
    for ch in "[]:*?/\\":
        name = name.replace(ch, "_")
    return name[:31]


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"database.db tidak ditemukan di {DB_PATH}. "
            "Jalankan `python src/load_to_sql.py` dulu."
        )

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    ringkasan_rows: list[dict] = []
    sheets: dict[str, pd.DataFrame] = {}

    # daily_sentiment sebagai referensi
    ds = pd.read_sql_query(
        "SELECT * FROM daily_sentiment ORDER BY tanggal;", conn
    )
    sheets["daily_sentiment"] = ds

    for periode_key, (start, end) in PERIODE.items():
        for ticker in TICKERS:
            df_h0 = pd.read_sql_query(
                SQL_SAMEDAY, conn, params=(ticker, start, end)
            )
            df_h1 = pd.read_sql_query(
                SQL_LAG_H1, conn, params=(ticker, start, end)
            )

            sheets[_sanitize_sheet(f"{periode_key}_{ticker}_H0")] = df_h0
            sheets[_sanitize_sheet(f"{periode_key}_{ticker}_H1")] = df_h1

            for mode, df in (("same_day_H0", df_h0), ("lag_H+1", df_h1)):
                pr, pp, sr, spv, n = _safe_corr(
                    df["skor_net_harian"], df["pct_change"]
                )
                ringkasan_rows.append({
                    "periode": periode_key,
                    "ticker": ticker,
                    "mode": mode,
                    "n_obs": n,
                    "pearson_r": pr,
                    "pearson_p": pp,
                    "spearman_r": sr,
                    "spearman_p": spv,
                    "mean_skor_net": df["skor_net_harian"].mean(),
                    "mean_pct_change": df["pct_change"].mean(),
                })

    conn.close()

    ringkasan = pd.DataFrame(ringkasan_rows)

    # Susun urutan sheet: ringkasan -> daily -> per periode/ticker
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
        ringkasan.to_excel(w, sheet_name="ringkasan_korelasi", index=False)
        sheets["daily_sentiment"].to_excel(
            w, sheet_name="daily_sentiment", index=False
        )
        for name, df in sheets.items():
            if name == "daily_sentiment":
                continue
            df.to_excel(w, sheet_name=name, index=False)

    print(f"[export] {OUT_XLSX}")
    print(f"[export] {len(sheets) + 1} sheet ditulis (termasuk ringkasan).")
    print("\n=== Ringkasan Korelasi ===")
    with pd.option_context("display.max_rows", None,
                           "display.float_format", "{:.4f}".format):
        print(ringkasan.to_string(index=False))


if __name__ == "__main__":
    main()
