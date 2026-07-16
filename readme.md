# Analisis Sentimen Berita Geopolitik terhadap Saham Siklikal

Script Python + SQLite untuk **Karya Tulis Ilmiah (KTI)** yang menganalisis
dampak berita geopolitik (Rusia-Ukraina 2022, Timur Tengah 2023-2024, dan
Perang Tarif 2025) terhadap pergerakan 4 saham siklikal Indonesia:
`ADRO.JK`, `ENRG.JK`, `ITMG.JK`, `BBCA.JK`.

Alur singkat:

```
scraping berita  ─►  preprocessing (Sastrawi)  ─►  scoring sentimen
                                                        │
                          yfinance ── harga saham ──────┤
                                                        ▼
                                    SQLite (JOIN same-day & JOIN lag H+1)
                                                        │
                                                        ▼
                                        Excel multi-sheet + ringkasan korelasi
```

---

## 1. Struktur folder

```
project/
├── data/
│   ├── raw_news/              # hasil scraping (CSV) — dihasilkan oleh scraper
│   ├── kamus/
│   │   ├── kamus_positif.txt  # 15 kata positif (mudah diperluas)
│   │   └── kamus_negatif.txt  # 15 kata negatif
│   └── output/
│       └── hasil_gabungan.xlsx   # output final (dihasilkan)
├── src/
│   ├── scraper_cnbc.py        # CNBC Indonesia (default: dummy realistis)
│   ├── scraper_investing.py   # Investing.com (default: dummy realistis)
│   ├── _dummy_dataset.py      # bank judul realistis per periode
│   ├── sentiment.py           # preprocessing Sastrawi + scoring kamus
│   ├── stock_fetch.py         # unduh yfinance (Open/High/Low/Close/Volume + pct_change)
│   ├── load_to_sql.py         # buat schema + insert ke database.db
│   └── join_export.py         # JOIN same-day & lag H+1, ekspor Excel + korelasi
├── run_pipeline.py            # orkestrator end-to-end
├── requirements.txt
├── database.db                # dihasilkan (SQLite)
└── README.md
```

---

## 2. Instalasi

```bash
cd project
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Python **3.11+** direkomendasikan.

---

## 3. Menjalankan pipeline

### Cara paling cepat (semua langkah otomatis):

```bash
python run_pipeline.py
```

Setelah selesai Anda akan mendapatkan:

- `database.db` – SQLite berisi tabel `news_sentiment`, `stock_prices`, dan
  view `daily_sentiment`
- `data/output/hasil_gabungan.xlsx` – Excel multi-sheet siap dipakai untuk
  grafik sidang KTI

Opsi berguna:

```bash
# lebih banyak berita per (sumber × periode)
python run_pipeline.py --per-periode 80

# skip scraping (pakai CSV yang sudah ada di data/raw_news)
python run_pipeline.py --skip-scrape

# skip unduh harga (kalau tidak ada internet ke Yahoo Finance)
python run_pipeline.py --skip-scrape --skip-stock
```

### Menjalankan modul satu per satu

```bash
cd src
python scraper_cnbc.py       # -> data/raw_news/cnbc_*.csv
python scraper_investing.py  # -> data/raw_news/investing_*.csv
python load_to_sql.py        # -> database.db
python join_export.py        # -> data/output/hasil_gabungan.xlsx
```

---

## 4. Tentang dataset berita

Default-nya kedua scraper memakai **dataset dummy realistis** yang dibundle
di `src/_dummy_dataset.py`. Alasannya:

- Arsip CNBC/Investing untuk 2022 dan 2023–2024 sering diblokir atau
  memerlukan Selenium; hasilnya sulit direproduksi ulang saat sidang.
- Judul-judul di dataset dummy dirancang **realistis** dan mengandung
  distribusi campuran kata positif/negatif/netral, sehingga skor sentimen
  yang dihasilkan tetap punya variasi yang bermakna untuk analisis JOIN
  H+1.

Bila ingin mencoba scraping riil (best-effort, tanpa Selenium):

```bash
python src/scraper_cnbc.py       --mode live
python src/scraper_investing.py  --mode live
```

Kalau situs menolak (mis. 403), gunakan mode dummy dan (opsional) tambah
judul-judul riil manual ke `_dummy_dataset.py`.

---

## 5. Kamus sentimen

- `data/kamus/kamus_positif.txt`
  → damai, stimulus, gencatan, ekspor, surplus, dovish, bantuan, subsidi,
    pemulihan, stabil, kondusif, kesepakatan, tumbuh, laba, meroket
- `data/kamus/kamus_negatif.txt`
  → inflasi, resesi, sanksi, boikot, tarif, perang, konflik, ketegangan,
    rudal, serangan, krisis, bunga, hawkish, panik, anjlok

Aturan skor:

```
skor_positif = jumlah kemunculan kata di kamus_positif.txt
skor_negatif = jumlah kemunculan kata di kamus_negatif.txt
skor_net     = skor_positif - skor_negatif
```

Kamus disimpan sebagai file `.txt` biasa sehingga bisa **diperluas tanpa
mengubah kode** — cukup tambah kata (1 kata per baris).

---

## 6. Schema SQLite

```sql
-- Tabel berita per baris (satu berita = satu baris)
CREATE TABLE news_sentiment (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal       TEXT NOT NULL,      -- YYYY-MM-DD
    sumber        TEXT NOT NULL,      -- 'CNBC' | 'Investing'
    judul         TEXT NOT NULL,
    url           TEXT,
    skor_positif  INTEGER,
    skor_negatif  INTEGER,
    skor_net      INTEGER
);

-- Tabel harga saham
CREATE TABLE stock_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal     TEXT NOT NULL,        -- YYYY-MM-DD
    ticker      TEXT NOT NULL,        -- 'ADRO.JK' | 'ENRG.JK' | 'ITMG.JK' | 'BBCA.JK'
    open, high, low, close  REAL,
    volume      INTEGER,
    pct_change  REAL,                 -- persen perubahan close vs close-1
    periode     TEXT                  -- label periode krisis
);

-- View agregasi harian (dipakai untuk JOIN)
CREATE VIEW daily_sentiment AS
SELECT tanggal,
       SUM(skor_positif) AS total_positif,
       SUM(skor_negatif) AS total_negatif,
       SUM(skor_net)     AS skor_net_harian,
       COUNT(*)          AS jumlah_berita
FROM news_sentiment
GROUP BY tanggal;
```

### Query utama

```sql
-- Same-day: sentimen T <-> harga T
SELECT ds.*, sp.close, sp.pct_change
FROM daily_sentiment ds
LEFT JOIN stock_prices sp
       ON sp.tanggal = ds.tanggal
      AND sp.ticker  = 'ADRO.JK';

-- Lag H+1: sentimen T <-> harga T+1
SELECT ds.tanggal AS tanggal_berita,
       sp.tanggal AS tanggal_harga,
       ds.skor_net_harian, sp.pct_change
FROM daily_sentiment ds
LEFT JOIN stock_prices sp
       ON sp.tanggal = DATE(ds.tanggal, '+1 day')
      AND sp.ticker  = 'ADRO.JK';
```

`LEFT JOIN` dipakai supaya tanggal libur bursa (harga saham kosong) tetap
tercatat di sisi berita.

---

## 7. Isi file Excel

`data/output/hasil_gabungan.xlsx` berisi:

| Sheet                              | Isi                                                                 |
| ---------------------------------- | ------------------------------------------------------------------- |
| `ringkasan_korelasi`               | Pearson & Spearman (skor_net_harian vs pct_change) per periode × ticker × mode |
| `daily_sentiment`                  | Agregasi harian sentimen                                            |
| `P1_2022_RusiaUkraina_ADRO.JK_H0`  | JOIN same-day untuk ADRO periode 1                                  |
| `P1_2022_RusiaUkraina_ADRO.JK_H1`  | JOIN lag H+1 untuk ADRO periode 1                                   |
| … dst 3 periode × 4 ticker × 2 mode = 24 sheet                                                       |

Di Excel tinggal `Insert → Chart → Scatter` pada kolom `skor_net_harian`
dan `pct_change` untuk membuat grafik dispersi yang dipakai di slide KTI.

---

## 8. Catatan

- Tanggal libur bursa: `LEFT JOIN` menjaga baris berita tetap ada, kolom
  harga akan `NULL`.
- Data 2025 dibatasi sampai tanggal berjalan (yfinance memberi sampai
  hari perdagangan terakhir).
- Kalau ingin mengganti/menambah ticker, edit `TICKERS` di
  `src/stock_fetch.py` **dan** `src/join_export.py`.
- Untuk memperluas kamus, cukup tambah kata di dua file `.txt` di
  `data/kamus/` — tidak perlu ubah kode.
