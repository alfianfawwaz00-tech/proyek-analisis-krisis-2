"""
_dummy_dataset.py
=================
Bank judul berita realistis berbahasa Indonesia untuk 3 periode krisis.
Digunakan oleh scraper_cnbc.py & scraper_investing.py sebagai fallback
ketika situs sumber memblokir request atau untuk keperluan reproducibility
sidang KTI.

Judul-judul di bawah SENGAJA mengandung kombinasi kata dari kamus
positif/negatif (dan banyak yang netral) agar distribusi skor sentimen
mendekati kondisi riil.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Bank judul per periode. Setiap list minimal ~40 judul yang akan
# dikombinasikan + dirotasi tanggalnya oleh generator.
# ---------------------------------------------------------------------------

JUDUL_P1_2022 = [
    "Rusia luncurkan rudal ke Kyiv, harga minyak dunia meroket",
    "Sanksi Uni Eropa terhadap Rusia perluas krisis energi",
    "Perang Rusia-Ukraina picu inflasi global tembus rekor",
    "The Fed sinyalkan bunga acuan naik agresif, pasar panik",
    "Boikot gas Rusia buat Eropa hadapi krisis energi musim dingin",
    "IHSG anjlok tersengat ketegangan geopolitik Eropa Timur",
    "Batu bara meroket, ADRO catat laba fantastis kuartal II",
    "Serangan drone hantam kilang minyak, harga Brent tembus USD 120",
    "Bank Indonesia naikkan suku bunga, sinyal hawkish menguat",
    "Krisis pangan global memburuk akibat perang di Ukraina",
    "Pemerintah beri subsidi BBM demi jaga daya beli masyarakat",
    "Kesepakatan ekspor gandum lewat Laut Hitam beri harapan pemulihan",
    "Ekspor batu bara Indonesia tumbuh dua digit di semester I",
    "Neraca perdagangan surplus, rupiah stabil di tengah gejolak",
    "Stimulus fiskal pemerintah dorong konsumsi rumah tangga",
    "Gencatan senjata singkat di Kherson beri sinyal damai",
    "BBCA bukukan laba bersih tumbuh dua digit",
    "ITMG raih laba rekor seiring lonjakan harga batu bara",
    "ENRG umumkan ekspansi tambang, saham meroket",
    "Konflik Rusia-Ukraina picu ketegangan pasokan pupuk global",
    "OPEC+ pangkas produksi, harga minyak mentah kembali panas",
    "Fed hawkish, wall street anjlok, IHSG ikut tertekan",
    "Rupiah stabil di kisaran 14.800 meski dolar menguat",
    "Sanksi baru AS terhadap perusahaan Rusia diberlakukan",
    "Pemulihan ekonomi Asia melambat imbas suku bunga tinggi",
    "Panik jual di bursa saham AS menular ke Asia",
    "Pemerintah percepat program bantuan langsung tunai",
    "Ekspor CPO Indonesia surplus, dorong penerimaan negara",
    "Krisis rantai pasok chip masih membayangi manufaktur",
    "Rudal balistik ditembakkan, ketegangan meningkat di Eropa Timur",
    "Kesepakatan damai belum tercapai, perang berlanjut",
    "Bank sentral global kompak hawkish tekan inflasi",
    "Serangan siber lumpuhkan pipa gas, harga energi melonjak",
    "Kondusif, aksi beli asing masuk ke saham perbankan",
    "Laba BBCA tumbuh berkat kredit konsumer",
    "Investor panik lepas aset berisiko jelang rapat Fed",
    "Subsidi listrik dilanjutkan untuk pelanggan rumah tangga kecil",
    "IHSG dibuka anjlok terseret bursa global",
    "Konflik meluas ke wilayah timur Ukraina",
    "Bank Indonesia optimistis pemulihan ekonomi berlanjut",
    "Tarif ekspor batu bara didiskusikan pemerintah",
    "Ekspor nikel tumbuh, mendukung surplus neraca dagang",
    "Boikot produk Rusia menyebar di Eropa",
    "Kesepakatan dagang RI-Korea beri sinyal kondusif",
    "Stimulus moneter dihentikan, pasar bereaksi negatif",
]

JUDUL_P2_2023_2024 = [
    "Serangan Hamas ke Israel picu konflik Timur Tengah",
    "Israel balas serangan, rudal menghantam Gaza",
    "Harga minyak meroket usai eskalasi Timur Tengah",
    "Fed pertahankan bunga tinggi, sinyal hawkish berlanjut",
    "IHSG anjlok terseret ketegangan geopolitik kawasan",
    "Sanksi baru AS terhadap entitas terkait Iran",
    "Ekspor batu bara Indonesia stabil meski permintaan melemah",
    "BBCA cetak laba bersih rekor sepanjang 2023",
    "Krisis Laut Merah ganggu rantai pasok global",
    "Serangan Houthi di Laut Merah picu lonjakan biaya logistik",
    "Bank Indonesia tahan suku bunga, sinyal dovish menguat",
    "Rupiah tertekan, dolar AS menguat tajam",
    "Konflik Israel-Hamas belum menunjukkan tanda gencatan",
    "Gencatan senjata sementara dicapai, sandera dibebaskan",
    "Pemulihan ekonomi China lambat, bebani harga komoditas",
    "Subsidi BBM tetap dipertahankan pemerintah",
    "ADRO umumkan dividen jumbo, saham meroket",
    "ITMG bagikan laba dalam bentuk dividen interim",
    "ENRG rugi kuartal III akibat harga minyak volatile",
    "Ekspor CPO ke India tumbuh, dorong surplus dagang",
    "Panik di pasar obligasi AS, imbal hasil melonjak",
    "Kesepakatan OPEC+ pangkas produksi kembali diperpanjang",
    "Inflasi AS lebih tinggi dari perkiraan, Fed kian hawkish",
    "Investor beralih ke aset aman di tengah krisis geopolitik",
    "Bank sentral global mulai sinyalkan pelonggaran",
    "Ketegangan Iran-Israel picu kekhawatiran perang meluas",
    "Serangan rudal Iran ke Israel, harga minyak Brent tembus USD 90",
    "Bantuan kemanusiaan untuk Gaza terhambat",
    "Stimulus fiskal China dorong optimisme pasar",
    "IHSG rebound seiring aliran modal asing masuk",
    "Rupiah stabil di 15.500, BI intervensi pasar",
    "BBCA umumkan kredit tumbuh dua digit",
    "Boikot produk terkait Israel meluas di Asia",
    "Kesepakatan dagang RI-Uni Eropa memasuki babak baru",
    "Ekspor batu bara ke Tiongkok surplus di kuartal IV",
    "Perang Rusia-Ukraina berlanjut, gandum tetap mahal",
    "Krisis properti China perburuk sentimen pasar",
    "Bank Indonesia surprise naikkan bunga, rupiah menguat",
    "Konflik di Lebanon selatan memanas",
    "Sanksi AS terhadap perusahaan minyak Rusia diperluas",
    "Anjlok! Harga nikel dunia jatuh ke titik terendah",
    "Kondusif, aliran dana asing masuk ke SBN",
    "Laba ITMG turun akibat harga batu bara melandai",
    "Dovish, ECB pertahankan bunga dan buka opsi pemangkasan",
    "Ketegangan di Selat Taiwan meningkat, saham Asia tertekan",
];

JUDUL_P3_2025 = [
    "Trump umumkan tarif impor 25 persen ke Tiongkok",
    "Perang tarif AS-China perluas ketegangan dagang global",
    "IHSG anjlok tersengat kebijakan tarif AS",
    "Boikot produk AS meluas di Tiongkok",
    "Bank Indonesia pertahankan suku bunga, sikap dovish menguat",
    "Ekspor nikel Indonesia surplus di kuartal I",
    "ADRO umumkan ekspansi tambang batu bara di Kalimantan",
    "Kesepakatan dagang RI-AS meredam kekhawatiran pasar",
    "Rupiah tembus 16.500, level terlemah sejak 1998",
    "Serangan drone di kilang Arab Saudi picu lonjakan minyak",
    "Krisis semikonduktor kembali menghantui manufaktur",
    "Pemerintah beri stimulus untuk sektor manufaktur",
    "Subsidi mobil listrik diperluas oleh pemerintah",
    "ITMG bagikan dividen final, saham meroket",
    "ENRG cetak laba positif berkat efisiensi biaya",
    "BBCA laporkan laba bersih tumbuh 12 persen",
    "Konflik Rusia-Ukraina memasuki fase gencatan senjata",
    "Kesepakatan damai parsial dicapai di Timur Tengah",
    "Fed pangkas bunga acuan, sinyal dovish kuat",
    "Panik jual asing tekan bursa saham Jakarta",
    "Ekspor CPO tumbuh dua digit di semester I 2025",
    "Neraca perdagangan surplus USD 3 miliar",
    "Inflasi Indonesia stabil di rentang target BI",
    "Tarif balasan Tiongkok picu kenaikan harga barang konsumsi",
    "Konflik dagang AS-Uni Eropa kian memanas",
    "Sanksi ekonomi baru dijatuhkan ke Iran",
    "Ketegangan di Semenanjung Korea meningkat kembali",
    "Rudal Korea Utara mendarat di Laut Jepang",
    "Serangan siber lumpuhkan bursa saham Asia sesaat",
    "Krisis energi kembali membayangi Eropa musim dingin",
    "Pemulihan ekonomi global masih rapuh, kata IMF",
    "Bantuan kemanusiaan disalurkan ke Gaza",
    "Kondusif, aliran dana asing kembali masuk ke SUN",
    "Bank sentral kompak dovish, aset berisiko menguat",
    "Perang tarif berlanjut, WTO peringatkan risiko resesi global",
    "Resesi ringan diprediksi melanda AS di semester II",
    "IHSG rebound, sektor perbankan pimpin penguatan",
    "ADRO catat produksi rekor batu bara di kuartal II",
    "Ekspor nikel ke AS terganggu tarif baru",
    "Kesepakatan tarif nol dicapai antara RI dan Australia",
    "Hawkish, Fed kembali naikkan bunga di luar dugaan",
    "Meroket, harga emas dunia tembus USD 3.000 per ons",
    "Krisis properti Tiongkok makin dalam, saham Asia tertekan",
    "Stimulus fiskal China dorong sentimen positif pasar",
    "Subsidi energi diperpanjang hingga akhir tahun",
    "Konflik Israel-Iran memanas, minyak Brent tembus USD 100",
];

PERIODE = {
    "P1": {
        "label": "2022_RusiaUkraina",
        "range": (date(2022, 2, 1), date(2022, 12, 31)),
        "judul": JUDUL_P1_2022,
    },
    "P2": {
        "label": "2023_2024_TimurTengah",
        "range": (date(2023, 10, 1), date(2024, 6, 30)),
        "judul": JUDUL_P2_2023_2024,
    },
    "P3": {
        "label": "2025_PerangTarif",
        "range": (date(2025, 1, 1), date(2025, 12, 31)),
        "judul": JUDUL_P3_2025,
    },
}


def _url_placeholder(sumber: str, judul: str, tgl: date) -> str:
    slug = hashlib.md5(judul.encode("utf-8")).hexdigest()[:10]
    host = "cnbcindonesia.com" if sumber == "CNBC" else "investing.com/id"
    return f"https://www.{host}/news/{tgl.strftime('%Y%m%d')}/{slug}"


def generate_dummy(sumber: str, periode_key: str,
                   berita_per_periode: int = 60,
                   seed: int = 42) -> pd.DataFrame:
    """Bangkitkan berita dummy realistis untuk satu sumber & satu periode."""
    rng = random.Random(f"{seed}-{sumber}-{periode_key}")
    info = PERIODE[periode_key]
    start, end = info["range"]
    bank = list(info["judul"])
    rng.shuffle(bank)

    total_hari = (end - start).days + 1
    rows = []
    for i in range(berita_per_periode):
        # Sebar tanggal merata + sedikit noise
        offset = int((i / max(berita_per_periode - 1, 1)) * (total_hari - 1))
        offset += rng.randint(-2, 2)
        offset = max(0, min(total_hari - 1, offset))
        tgl = start + timedelta(days=offset)

        judul = bank[i % len(bank)]
        # Variasi ringan (prefix sumber) supaya judul CNBC vs Investing tidak identik
        if sumber == "Investing":
            judul_final = judul
        else:
            judul_final = judul

        rows.append({
            "tanggal": tgl.strftime("%Y-%m-%d"),
            "sumber": sumber,
            "judul": judul_final,
            "url": _url_placeholder(sumber, judul_final, tgl),
        })

    df = pd.DataFrame(rows)
    return df.sort_values("tanggal").reset_index(drop=True)
