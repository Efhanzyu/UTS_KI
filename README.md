# Brankas File Tugas Kuliah

Aplikasi Flask untuk mengenkripsi dan mendekripsi teks serta file dengan AES-256-GCM atau ChaCha20-Poly1305. Password diproses melalui PBKDF2-HMAC-SHA256 dan tidak disimpan di repositori atau database.

## Anggota Kelompok

| Nama | NPM |
|---|---|
| [NAMA ANGGOTA 1] | [NPM ANGGOTA 1] |
| [NAMA ANGGOTA 2] | [NPM ANGGOTA 2] |

> Catatan: data nama dan NPM belum ditemukan di repository aktif. Silakan isi bagian di atas secara manual sesuai identitas kelompok yang sebenarnya sebelum presentasi atau pengumpulan final.

## Fitur utama

- Enkripsi teks dengan AES-256-GCM atau ChaCha20-Poly1305
- Dekripsi teks dengan validasi tag autentikasi
- Enkripsi file ke format container .enc
- Dekripsi file dengan pengecekan integritas ciphertext
- PBKDF2-HMAC-SHA256 dengan salt acak
- Benchmark performa untuk algoritma AES dan ChaCha20
- Analisis entropy, histogram, dan avalanche effect
- Sample file dalam folder test_files untuk validasi roundtrip

## Persiapan local

Requirements: Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Salin .env.example menjadi .env, lalu isi nilai yang dibutuhkan. File .env tidak boleh di-commit.

```bash
copy .env.example .env
```

## Environment variables

```text
SECRET_KEY=
FLASK_ENV=development
PBKDF2_ITERATIONS=600000
MAX_CONTENT_MB=50

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=brankas-files

BENCHMARK_KDF_ITERATIONS=1000
BENCHMARK_RUNS=10
```

`SECRET_KEY` wajib diisi saat production. `SUPABASE_SERVICE_ROLE_KEY` hanya boleh ada di server-side environment, bukan di frontend atau repositori.

## Menjalankan aplikasi

```bash
python app.py
```

Setelah server berjalan, buka:

- http://127.0.0.1:5000/
- http://127.0.0.1:5000/text
- http://127.0.0.1:5000/file
- http://127.0.0.1:5000/benchmark

## Contoh Penggunaan

### A. Enkripsi file

1. Buka halaman file atau endpoint /api/encrypt/file.
2. Pilih file yang ingin dienkripsi, misalnya laporan.pdf.
3. Masukkan password.
4. Sistem menghasilkan file dengan ekstensi .enc.
5. Metadata file asli seperti nama file dan MIME type disimpan di header container dan tidak dipublikasikan dalam plaintext.

Contoh body form-data untuk API:

```text
file: laporan.pdf
password: SandiRahasia123!
algorithm: AES-256-GCM
```

Hasilnya adalah file .enc yang siap diunduh untuk penyimpanan aman.

### B. Dekripsi file

1. Pilih file .enc.
2. Masukkan password yang sama saat enkripsi.
3. Sistem melakukan derivasi key PBKDF2 lalu memverifikasi tag autentikasi.
4. Jika berhasil, file asli dikembalikan untuk diunduh.

Contoh body form-data:

```text
file: laporan.pdf.enc
password: SandiRahasia123!
```

### C. Password salah

Jika password tidak cocok, proses dekripsi akan ditolak dengan respons error generik. Tujuannya adalah mencegah adanya pengungkapan apakah kesalahan berasal dari password salah atau ciphertext yang dimodifikasi.

### D. Ciphertext tampered

Jika ciphertext atau metadata berubah, tag autentikasi gagal saat dekripsi. Sistem akan menolak file tersebut dan mengembalikan error yang menandakan data tidak valid.

### E. Enkripsi teks

Endpoint yang tersedia:

```http
POST /api/encrypt/text
Content-Type: application/json
```

Body contoh:

```json
{
  "plaintext": "Tugas kuliah keamanan informasi",
  "password": "SandiRahasia123!",
  "algorithm": "AES-256-GCM"
}
```

Response contoh:

```json
{
  "success": true,
  "message": "Enkripsi berhasil.",
  "data": {
    "ciphertext_b64": "...",
    "algorithm": "AES-256-GCM",
    "kdf": "PBKDF2-HMAC-SHA256",
    "pbkdf2_iterations": 600000,
    "salt_size_bytes": 16,
    "nonce_size_bytes": 12,
    "ciphertext_size_bytes": 52
  }
}
```

Dekripsi teks:

```http
POST /api/decrypt/text
Content-Type: application/json
```

```json
{
  "ciphertext_b64": "...",
  "password": "SandiRahasia123!"
}
```

Output yang dikembalikan berisi plaintext asli.

## API yang tersedia

Berikut endpoint utama berdasarkan source code saat ini:

- GET /api/health
- POST /api/encrypt/text
- POST /api/decrypt/text
- POST /api/encrypt/file
- POST /api/decrypt/file
- GET /api/storage/files
- GET /api/storage/files/<file_id>
- POST /api/storage/files/<file_id>/decrypt
- DELETE /api/storage/files/<file_id>
- POST /api/benchmark
- POST /api/benchmark/export/csv
- POST /api/benchmark/export/excel

## Benchmark

Aplikasi menyediakan benchmark performa untuk AES-256-GCM dan ChaCha20-Poly1305 pada ukuran yang umum:

- 1 KB
- 1 MB
- 10 MB

Script yang tersedia:

```bash
python scripts/run_benchmark.py
```

Ekspor hasil benchmark ke CSV/XLSX:

```bash
python scripts/export_results.py
```

Hasil file benchmark disimpan di folder results.

## Sample files

Folder test_files berisi file sampel untuk validasi roundtrip, termasuk format PDF, PNG, JPG, dokumen, dan file berukuran lebih besar.

## Testing

```bash
python -m pytest -q
```

Suite pengujian mencakup keamanan, container, roundtrip, file encryption, benchmark export, dan regresi acceptance.

## Security notes

- Password tidak disimpan.
- Salt dibuat acak per enkripsi.
- Nonce dibuat acak per enkripsi.
- Tag autentikasi diperiksa saat dekripsi.
- Secret dan credential tidak boleh masuk ke repositori.
- File .env harus diproteksi dan dikelola melalui environment variable server.

## Deployment notes

Project ini dapat dikonfigurasi untuk deployment lokal maupun platform seperti Render atau Vercel. Gunakan env var yang benar dan jangan menaruh secret asli ke file source atau file deployment config.
