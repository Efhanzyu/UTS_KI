# Prosedur Pengujian & Validasi — Brankas File Tugas Kuliah

Dokumentasi ini menjelaskan rencana pengujian otomatis, metodologi benchmark, dan skenario verifikasi integritas data.

---

## 1. Pengujian Otomatis (Automated Unit Testing)

Pengujian unit menggunakan framework `pytest` yang mencakup skenario unit, acceptance, keamanan, whitespace teks, dan roundtrip sepuluh berkas sampel. Jumlah aktual dapat dilihat pada output pytest.

### Menjalankan Seluruh Unit Test:
```bash
python -m pytest tests/ -v
```

### Cakupan Pengujian:
1. **`tests/test_kdf.py`**:
   - Validasi panjang salt (32 bytes).
   - Validasi sifat CSPRNG (dua pemanggilan menghasilkan nilai acak berbeda).
   - Validasi panjang key PBKDF2 (32 bytes).
   - Determinisme: password, salt, dan iterasi yang sama menghasilkan key identik.
   - Non-determinisme: perubahan password, salt, atau iterasi menghasilkan key berbeda.
2. **`tests/test_aes.py`**:
   - Validasi panjang nonce AES-256-GCM (12 bytes).
   - Enkripsi dan dekripsi roundtrip mengembalikan plaintext identik.
   - Verifikasi penolakan dekripsi dengan kunci yang salah (`InvalidTag`).
   - Verifikasi penolakan dekripsi dengan nonce yang salah (`InvalidTag`).
   - Verifikasi penolakan ciphertext yang telah dimodifikasi (tampering detection).
3. **`tests/test_chacha.py`**:
   - Pengujian setara untuk ChaCha20-Poly1305 (nonce, roundtrip, wrong key, wrong nonce, tampering).
4. **`tests/test_container.py`**:
   - Validasi serialisasi binary container (`pack_encrypted_file`) dan deserialisasi (`unpack_encrypted_file`).
   - Penolakan file dengan Magic bytes yang salah (`MagicError`).
   - Penolakan versi kontainer tidak dikenal (`VersionError`).
   - Penolakan header yang rusak atau file terpotong (`MetadataError`).
   - Penolakan algoritma tidak didukung (`AlgorithmError`).
5. **`tests/test_file_encryption.py`**:
   - Enkripsi teks dan file untuk kedua algoritma (AES-256-GCM & ChaCha20-Poly1305).
   - Pengujian pemulihan nama file asli dan MIME type.
   - Penolakan password salah pada file enkripsi.
6. **`tests/test_security.py`**:
   - Validasi input (password panjang ekstrem, plaintext kosong, dll).
   - Sanitasi nama file dan pencegahan serangan Path Traversal (`../../etc/passwd`).
   - Verifikasi response error API tidak membocorkan stack trace Python.
   - Endpoint health check.

---

## 2. Pengujian Benchmark Kuantitatif

Metrik performa yang diuji:
1. **Waktu Eksekusi (Encryption & Decryption Time)**:
   - Diuji pada ukuran 1 KB, 1 MB, dan 10 MB dengan beberapa pengulangan untuk memperoleh nilai rata-rata, minimum, dan maksimum.
2. **Waktu derivasi kunci (PBKDF2)**:
   - Diukur terpisah dari operasi AEAD dengan jumlah iterasi konfigurasi production.
3. **Avalanche Effect**:
   - Mengukur perubahan ciphertext untuk mutasi satu bit plaintext dan satu bit key dalam eksperimen terpisah.
   - Rumus: Avalanche (%) = (changed bits / total bits) * 100%.
   - Nonce tetap hanya dipakai dalam eksperimen terkontrol untuk mengisolasi mutasi; nonce tidak pernah dipakai ulang pada enkripsi produksi.
4. **Shannon Entropy**:
   - Mengukur ketidakpastian informasi dalam skala 0.0 hingga 8.0 bit/byte.
   - Nilai entropy adalah statistik distribusi sampel dan tidak membuktikan keamanan cipher.
5. **Distribusi Nilai Byte (Histogram 0–255)**:
   - Membandingkan sebaran frekuensi kemunculan byte antara plaintext dan ciphertext.

### Menjalankan Benchmark CLI:
```bash
python scripts/run_benchmark.py
```

### Ekspor Hasil Benchmark ke CSV & Excel (XLSX):
```bash
python scripts/export_results.py
```
File hasil tersimpan di direktori `results/`:
- `results/benchmark_results.csv`
- `results/benchmark_results.xlsx`

---

## 3. Skenario Pengujian Manual (User Acceptance Testing)

1. **Jalankan Aplikasi Web**:
   ```bash
   python app.py
   ```
   Akses `http://127.0.0.1:5000` pada peramban web.
2. **Skenario 1 — Enkripsi Teks**:
   - Masukkan pesan tugas kuliah.
   - Pilih algoritma AES-256-GCM atau ChaCha20-Poly1305.
   - Masukkan password dan klik *Enkripsi*.
   - Salin ciphertext Base64, buka tab *Dekripsi*, masukkan password yang sama, lalu klik *Dekripsi*. Teks asli harus kembali utuh.
3. **Skenario 2 — Enkripsi File Dokumen**:
   - Buka menu *Enkripsi File*.
   - Drag & drop salah satu file dari direktori `test_files/` (misalnya `04_laporan_praktikum.pdf`).
   - Masukkan password dan enkripsi. Download file `.enc`.
   - Unggah file `.enc` tersebut ke form *Dekripsi File*, masukkan password, lalu klik *Dekripsi File*.
   - Buka file PDF hasil dekripsi dan pastikan dokumen dapat dibuka secara sempurna.
4. **Skenario 3 — Uji Integritas & Tamper**:
   - Buka file `.enc` dengan text editor atau hex editor dan ubah 1 karakter di bagian akhir file.
   - Lakukan dekripsi file yang telah diubah tersebut.
   - Sistem harus menampilkan pesan error generik dan menolak mendekripsi data yang telah rusak.
