"""
sentiment.py
=============
Preprocessing berita berbahasa Indonesia (Sastrawi) + scoring
sentimen dictionary-based (+1 kata positif, -1 kata negatif).

Input : CSV mentah hasil scraping (kolom: tanggal, sumber, judul, url)
Output: DataFrame `news_sentiment` per berita, dan agregasi harian.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

BASE_DIR = Path(__file__).resolve().parent.parent
KAMUS_DIR = BASE_DIR / "data" / "kamus"


def load_kamus(path: Path) -> set[str]:
    """Muat kamus sentimen (satu kata per baris)."""
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


# Inisialisasi Sastrawi sekali saja (mahal)
_stemmer = StemmerFactory().create_stemmer()
_stopword = StopWordRemoverFactory().create_stop_word_remover()

KAMUS_POSITIF = load_kamus(KAMUS_DIR / "kamus_positif.txt")
KAMUS_NEGATIF = load_kamus(KAMUS_DIR / "kamus_negatif.txt")


def preprocess(teks: str) -> list[str]:
    """Case folding -> hapus non-alfabet -> stopword removal -> stemming."""
    if not isinstance(teks, str):
        return []
    teks = teks.lower()
    teks = re.sub(r"[^a-z\s]", " ", teks)
    teks = re.sub(r"\s+", " ", teks).strip()
    teks = _stopword.remove(teks)
    teks = _stemmer.stem(teks)
    return teks.split()


def hitung_skor(tokens: Iterable[str]) -> tuple[int, int, int]:
    """Return (skor_positif, skor_negatif, skor_net)."""
    pos = sum(1 for t in tokens if t in KAMUS_POSITIF)
    neg = sum(1 for t in tokens if t in KAMUS_NEGATIF)
    return pos, neg, pos - neg


def skor_dataframe(df_berita: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan kolom skor sentimen ke DataFrame berita."""
    df = df_berita.copy()
    df["tanggal"] = pd.to_datetime(df["tanggal"]).dt.strftime("%Y-%m-%d")
    tokens = df["judul"].apply(preprocess)
    skor = tokens.apply(hitung_skor)
    df["skor_positif"] = skor.apply(lambda x: x[0])
    df["skor_negatif"] = skor.apply(lambda x: x[1])
    df["skor_net"] = skor.apply(lambda x: x[2])
    return df[["tanggal", "sumber", "judul", "url",
               "skor_positif", "skor_negatif", "skor_net"]]


def agregasi_harian(df_skor: pd.DataFrame) -> pd.DataFrame:
    """Agregasi skor per tanggal (untuk JOIN dengan harga saham)."""
    agg = (
        df_skor.groupby("tanggal")
        .agg(
            total_positif=("skor_positif", "sum"),
            total_negatif=("skor_negatif", "sum"),
            skor_net_harian=("skor_net", "sum"),
            jumlah_berita=("judul", "count"),
        )
        .reset_index()
        .sort_values("tanggal")
    )
    return agg


if __name__ == "__main__":
    # Demo: proses semua CSV di data/raw_news
    raw_dir = BASE_DIR / "data" / "raw_news"
    csvs = sorted(raw_dir.glob("*.csv"))
    if not csvs:
        print("Tidak ada CSV di data/raw_news. Jalankan scraper dulu.")
    else:
        dfs = [pd.read_csv(p) for p in csvs]
        df_all = pd.concat(dfs, ignore_index=True)
        df_skor = skor_dataframe(df_all)
        agg = agregasi_harian(df_skor)
        print(f"Total berita     : {len(df_skor)}")
        print(f"Total hari unik  : {len(agg)}")
        print(agg.head(10).to_string(index=False))
