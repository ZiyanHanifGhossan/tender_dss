# Tender DSS

Sistem pendukung keputusan tender sederhana berbasis Streamlit, scoring, dan Machine Learning (Logistic Regression).

## Fitur utama

- Input / simpan data tender ke SQLite
- Tandai hasil tender (Menang / Kalah)
- Prediksi peluang menang menggunakan model ML dengan opsi melihat perhitungan detail
- Retrain model menggunakan data berlabel (dengan evaluasi)
- Hapus tender, dan model disimpan ke `models/pipeline.joblib`

## Quick start 🔧

1. Pasang dependensi (direkomendasikan virtual environment):

```bash
# Pilihan 1: manual (aktifkan venv lalu install)
python -m pip install -r requirements.txt

# Pilihan 2: gunakan helper script untuk membuat venv dan install (direkomendasikan untuk pengguna lain)
# PowerShell (Windows):
.\scripts\setup_env.ps1
# Bash (Linux/macOS):
./scripts/setup_env.sh

# Atau cukup jalankan helper start script yang otomatis membuat venv dan menginstall sebelum start:
# Windows cmd: double-click `start_streamlit.bat` atau jalankan `start_streamlit.bat`
# PowerShell: `./start_streamlit.ps1`
```

2. Inisialisasi database dan contoh data (opsional):

```bash
python scripts/init_db.py
```

3. Jalankan aplikasi Streamlit:

```bash
# Pastikan Anda berada di virtual environment proyek.
# Contoh (PowerShell):
.\.venv\Scripts\Activate.ps1
# Contoh (cmd):
.\.venv\Scripts\activate

# Lalu jalankan Streamlit dengan Python proyek:
python -m streamlit run app.py
```

> **Catatan:** Visualisasi interaktif pada halaman **Tender Pipeline** memerlukan package tambahan: **plotly**. Instal dengan:
>
> ```bash
> pip install plotly
> ```
> atau jalankan `pip install -r requirements.txt` jika Anda mengikuti langkah Quick start.

4. Gunakan menu di sidebar:
- "Input Tender" untuk menambahkan atau menghapus data
- "Tandai Hasil Tender" untuk memberi label Menang/Kalah
- "Retrain Model" untuk melatih ulang model dengan data berlabel
- "ML Prediction" untuk membuat prediksi berdasarkan tender tersimpan atau input manual

## Menjalankan test 🔬

Project memiliki beberapa test pytest sederhana untuk memeriksa schema DB dan retrain model.

```bash
python -m pytest tests
```

## Continuous Integration (CI)

Project sudah berisi workflow GitHub Actions di `.github/workflows/ci.yml` yang akan:
- Install dependencies
- Menjalankan `scripts/init_db.py`
- Menjalankan test suite (`pytest`)

## Catatan teknis 💡
- Model disimpan di `models/pipeline.joblib` setelah retrain.
- Perhitungan **Tender Gugur (NO BID)** pada halaman *Tender Pipeline* mengikuti logika pada menu **Pre-Qualification & Bid Decision** (yaitu pengecekan pre-qualification, total score >= 0.6, dan risiko tidak tinggi).
- Jika Anda ingin retrain secara otomatis, tambahkan data berlabel (outcome) pada tabel `tender`.

## Kontribusi

Silakan buka issue atau PR untuk fitur baru atau perbaikan. Pastikan menambahkan test bila menambah fungsi kritis.


## Aktifkan Domain
- Salin perintah ini ke terminal.
```bash
cloudflared tunnel run streamlit-private
```
---

```bash
# Pastikan menggunakan Python proyek/virtualenv:
python -m streamlit run app.py

Atau gunakan helper script (Windows):

* Double-click `start_streamlit.bat` atau jalankan dari cmd:
  `start_streamlit.bat`
* Atau jalankan dari PowerShell:
  `.\start_streamlit.ps1`
```


