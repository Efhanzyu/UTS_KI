# Brankas File Tugas Kuliah

Aplikasi Flask untuk enkripsi dan dekripsi teks serta file menggunakan AES-256-GCM atau ChaCha20-Poly1305. Password diturunkan dengan PBKDF2-HMAC-SHA256; password dan encryption key tidak disimpan.

## Pemrosesan File

File upload dibaca ke memory, dienkripsi atau didekripsi selama request, lalu dikirim langsung sebagai download. Aplikasi tidak menyimpan hasil secara permanen dan tidak memerlukan database. Format container `.enc` tetap membawa metadata algoritma, parameter PBKDF2, salt, nonce, ciphertext, dan authentication tag.

```text
Browser → Flask → Encrypt / Decrypt di memory → Download
```

## Menjalankan Aplikasi

Requirements: Python 3.11+.

```bash
git clone https://github.com/Efhanzyu/UTS_KI.git
cd UTS_KI
python -m venv .venv
```

Aktifkan virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Pasang dependency dan jalankan:

```bash
pip install -r requirements-dev.txt
python app.py
```

Buka `http://127.0.0.1:5000`. `.env.example` dapat disalin menjadi `.env` untuk konfigurasi lokal. `SECRET_KEY` opsional dalam development; tetapkan secret acak melalui environment variable untuk deployment production. Jangan commit `.env`.

## Environment

| Variable | Default | Keterangan |
| --- | --- | --- |
| `SECRET_KEY` | acak saat development | Wajib ditetapkan pada production |
| `FLASK_ENV` | `development` | Gunakan `production` saat deployment |
| `PORT` | `5000` | Port server |
| `MAX_CONTENT_MB` | `64` | Batas ukuran upload |
| `PBKDF2_ITERATIONS` | `600000` | Iterasi KDF untuk operasi aplikasi |
| `BENCHMARK_KDF_ITERATIONS` | `1000` | Iterasi KDF benchmark |
| `BENCHMARK_RUNS` | `10` | Jumlah pengulangan benchmark |

## Deployment

Entry point production adalah `app:app`; gunakan Gunicorn pada platform Linux:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

Vercel menggunakan `api/index.py` melalui `vercel.json`. Filesystem serverless bersifat sementara; aplikasi ini tidak mengandalkan penyimpanan file antarrekuest. Hasil enkripsi dan dekripsi dikirim langsung sebagai response download.

## Benchmark dan Pengujian

Jalankan seluruh test:

```bash
python -m pytest -q
```

Jalankan benchmark dan ekspor hasil:

```bash
python scripts/run_benchmark.py
python scripts/export_results.py
```

Benchmark membandingkan AES-256-GCM dan ChaCha20-Poly1305 untuk ukuran 1 KB, 1 MB, dan 10 MB. Analisis juga mencakup avalanche effect, entropy, dan histogram byte. Sepuluh file contoh untuk roundtrip tersedia di `test_files/`.

## Anggota Kelompok

| No. | Nama | NPM |
| --- | --- | --- |
| 1 | Parhan | 247006111183 |
| 2 | Muhammad Kent Faiq Arifien | 247006111192 |
| 3 | Rahman Riana Zulfikri | 247006111188 |
