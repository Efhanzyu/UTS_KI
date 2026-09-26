# Brankas File Tugas Kuliah

Aplikasi Flask untuk mengenkripsi dan mendekripsi teks serta file dengan AES-256-GCM atau ChaCha20-Poly1305. Password diproses melalui PBKDF2-HMAC-SHA256 dan tidak disimpan.

## Local Development

Requirements: Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py
```

Buka `http://127.0.0.1:5000`. Salin `.env.example` menjadi `.env` untuk konfigurasi lokal. Isi `SECRET_KEY` dengan nilai acak; file `.env` tidak boleh di-commit.

## Production Deployment

Production entry point adalah `app:app` dan server production menggunakan Gunicorn:

```bash
gunicorn app:app
```

Untuk deployment, Gunicorn menerima `PORT` dari platform dan aplikasi berjalan dengan `FLASK_ENV=production`. Jangan menjalankan Flask development server sebagai server production.

Gunicorn menggunakan dependency Unix `fcntl` dan tidak dapat dijalankan native pada Windows. Gunakan `python app.py` untuk local testing di Windows; Render menjalankan Gunicorn pada environment Linux.

Runtime dependencies berada di `requirements.txt`. Dependency test dan script pengembangan berada di `requirements-dev.txt`.

### Environment Variables

```text
SECRET_KEY=
FLASK_ENV=production
PORT=10000
MAX_CONTENT_MB=64
PBKDF2_ITERATIONS=600000
BENCHMARK_KDF_ITERATIONS=1000
BENCHMARK_RUNS=10
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=brankas-files
```

`SECRET_KEY` wajib diisi pada production. `SUPABASE_SERVICE_ROLE_KEY` harus berisi Supabase Secret API key (`sb_secret_...`) dan hanya boleh berada di backend environment variable. `SUPABASE_STORAGE_BUCKET` berisi nama bucket saja, yaitu `brankas-files`. Project ini tidak memiliki fitur hybrid RSA; karena itu `RSA_PRIVATE_KEY_PATH` tidak diperlukan.

## Deploy to Render

1. Push repository ke GitHub.
2. Login ke Render.
3. Pilih **New Web Service**.
4. Hubungkan repository GitHub.
5. Pilih branch `main`.
6. Gunakan build command `pip install -r requirements.txt`.
7. Gunakan start command `gunicorn --bind 0.0.0.0:$PORT app:app`.
8. Set `FLASK_ENV=production` dan `SECRET_KEY` sebagai environment variable.
9. Deploy service.
10. Buka URL Render yang diberikan.

File `render.yaml` menyediakan konfigurasi yang sama dan membuat `SECRET_KEY` melalui secret Render. Jangan menulis secret aktual di repository atau `render.yaml`.

## File Storage

Endpoint file membaca upload ke memory dan mengirim hasil melalui response `send_file` dari `io.BytesIO`. Tidak ada upload, hasil enkripsi, atau hasil dekripsi yang disimpan sebagai file permanen. Filesystem Render bersifat ephemeral dan tidak boleh dianggap sebagai vault persisten.

Batas upload dikontrol oleh `MAX_CONTENT_MB` dan nama file dibersihkan dengan `secure_filename`. Hasil download hanya hidup selama response berlangsung.

## Deployment Smoke Test

- `GET /`
- `GET /api/health`
- Enkripsi teks lalu dekripsi teks
- Enkripsi file lalu dekripsi file
- Password salah ditolak
- Ciphertext yang dimodifikasi ditolak
- Benchmark berjalan setelah data pengujian dikirim

Health check mengembalikan HTTP 200 dengan pesan `Brankas API is running`.

## Deploy to Vercel

Project ini menggunakan `api/index.py` sebagai serverless WSGI entry point dan `vercel.json` untuk meneruskan seluruh route ke Flask.

1. Push repository ke GitHub.
2. Login ke Vercel dan pilih **Add New Project**.
3. Import repository `Efhanzuyu/UTS_KI` dari branch `main`.
4. Biarkan Vercel membaca konfigurasi dari `vercel.json`.
5. Tambahkan environment variables berikut pada Production:
	- `FLASK_ENV=production`
	- `SECRET_KEY=<generate a long random secret in Vercel>
	- `MAX_CONTENT_MB=64`
	- `PBKDF2_ITERATIONS=600000`
	- `BENCHMARK_KDF_ITERATIONS=1000`
	- `BENCHMARK_RUNS=10`
6. Deploy project dan buka domain Vercel.
7. Verifikasi `GET /api/health` mengembalikan HTTP 200.

Jangan memasukkan nilai secret ke `vercel.json`, source code, atau repository. Vercel Functions memiliki filesystem ephemeral; aplikasi ini hanya memproses upload selama request dan mengirim hasil sebagai download response.

## Supabase Storage Setup

1. Buat project baru di Supabase.
2. Buka **Storage** dan buat bucket `brankas-files`.
3. Set bucket sebagai **Private**, bukan public.
4. Salin Project URL ke `SUPABASE_URL`.
5. Salin server-side Secret API key (`sb_secret_...`) ke `SUPABASE_SERVICE_ROLE_KEY` pada Vercel. Jangan gunakan publishable key.
6. Set `SUPABASE_STORAGE_BUCKET=brankas-files`.
7. Redeploy Vercel.

Service role key hanya digunakan oleh Flask backend. Browser tidak menerima key tersebut. Object dienkripsi lebih dulu sebelum diunggah ke path server-generated `users/<session-id>/<file-id>.enc`. Session ID membatasi daftar, download, decrypt, dan delete ke browser owner yang sama.

Metadata file dibaca dari header container `.enc`; tidak ada password atau encryption key yang disimpan. Plaintext tidak pernah diunggah ke Supabase dan hasil dekripsi hanya dikirim dari memory sebagai response.

## Testing

```bash
python -m pytest -q
```

Test suite mencakup algoritma AES-GCM, ChaCha20-Poly1305, PBKDF2, container, encoding, keamanan input, roundtrip file, dan acceptance regression.