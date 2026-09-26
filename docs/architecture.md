# Arsitektur Sistem — Brankas File Tugas Kuliah

## 1. Ikhtisar Sistem

**Brankas File Tugas Kuliah** adalah aplikasi web berbasis Python (Flask) dan JavaScript Vanilla yang dirancang untuk mengamankan data akademik mahasiswa (teks laporan, tugas kuliah, dokumen PDF, DOCX, kode sumber, dan gambar) menggunakan algoritma kriptografi modern terotentikasi (Authenticated Encryption with Associated Data - AEAD).

---

## 2. Diagram Alur Data & Arsitektur

```
+------------------------------------------------------------------+
|                     User Browser (Frontend)                      |
|   HTML5 + Vanilla CSS (Dark Theme) + Vanilla JS (No External)    |
|   - Dashboard (index.html)    - Enkripsi File (file.html)        |
|   - Enkripsi Teks (text.html) - Benchmark & Visualisasi          |
+---------------------------------+--------------------------------+
                                  | HTTP / JSON / Multipart
                                  v
+------------------------------------------------------------------+
|                  Flask Application Layer (app/)                  |
|   - app.py & config.py: Konfigurasi, Security Limit (64 MB)      |
|   - routes/pages.py: Rendering Template Jinja2                   |
|   - routes/api.py: Restful JSON API & File Streaming             |
|   - utils/security.py: Sanitasi Input, Anti-Path Traversal       |
|   - utils/encoding.py: Safe Base64 Helper                        |
+---------------------------------+--------------------------------+
                                  |
                                  v
+------------------------------------------------------------------+
|                    Services Layer (app/services)                 |
|   - encryption_service.py: Orkestrasi Alur Kriptografi           |
|   - file_service.py: Sanitasi Nama File & Deteksi MIME           |
|   - benchmark_service.py: Pengukuran Waktu, Avalanche, Entropy   |
+---------------------------------+--------------------------------+
                                  |
                                  v
+------------------------------------------------------------------+
|                     Crypto Core (app/crypto)                     |
|   - kdf.py: PBKDF2-HMAC-SHA256 (Salt 32B, Iterasi Default 600K)  |
|   - aes_gcm.py: AES-256-GCM (Nonce 12B, Tag Autentikasi 16B)     |
|   - chacha20.py: ChaCha20-Poly1305 (Nonce 12B, Tag Poly1305 16B)|
|   - container.py: Serialisasi Binary Container (.enc)            |
+------------------------------------------------------------------+
```

---

## 3. Komponen Kriptografi

### A. Key Derivation Function (KDF): PBKDF2-HMAC-SHA256
- **Standar**: NIST SP 800-132.
- **Tujuan**: Mengubah password teks dari pengguna menjadi kunci simetris 256-bit (32 bytes) yang kuat.
- **Salt**: 32 bytes acak dihasilkan menggunakan CSPRNG (`os.urandom`). Setiap file atau teks memiliki salt yang unik sehingga mencegah serangan Rainbow Table.
- **Iterasi**: 600.000 putaran (default) untuk meningkatkan computational cost bagi penyerang brute force.

### B. AES-256-GCM (Galois/Counter Mode)
- **Standar**: NIST SP 800-38D.
- **Mode**: Authenticated Encryption with Associated Data (AEAD).
- **Kunci**: 256-bit (32 bytes).
- **Nonce (IV)**: 12 bytes (96-bit) unik per operasi.
- **Authentication Tag**: 16 bytes (128-bit) yang menjamin integritas (integrity) dan keaslian (authenticity). Modifikasi sekecil 1 bit pada ciphertext akan menyebabkan dekripsi ditolak seketika (`InvalidTag`).

### C. ChaCha20-Poly1305
- **Standar**: RFC 8439 (IETF).
- **Cipher**: ChaCha20 stream cipher dengan 20 putaran.
- **MAC**: Poly1305 128-bit authenticator.
- **Keunggulan**: Memberikan performa sangat tinggi pada arsitektur perangkat bergerak atau prosesor tanpa akselerasi perangkat keras AES-NI.

---

## 4. Struktur Format Kontainer File `.enc`

Format biner mandiri (self-contained) yang memuat metadata penting untuk dekripsi tanpa menyimpan password atau kunci:

```
+------------+------------+---------------+----------------------+------------------------+
| Offset (B) | Ukuran (B) | Tipe Data     | Field                | Keterangan             |
+------------+------------+---------------+----------------------+------------------------+
| 0          | 8          | Bytes         | MAGIC                | b"BRANKAS\x01"         |
| 8          | 2          | uint16 (BE)   | VERSION              | b"\x00\x01" (v1)       |
| 10         | 4          | uint32 (BE)   | HEADER_LEN           | Panjang Header JSON    |
| 14         | N          | UTF-8 JSON    | HEADER METADATA      | Parameter KDF & Algoritma
| 14 + N     | Sisa Bytes | Binary        | CIPHERTEXT + AEAD TAG| Data Terenkripsi       |
+------------+------------+---------------+----------------------+------------------------+
```

### Isi Metadata JSON:
```json
{
  "version": "1",
  "algorithm": "AES-256-GCM",
  "kdf": "PBKDF2-HMAC-SHA256",
  "pbkdf2_iterations": 600000,
  "salt_b64": "...",
  "nonce_b64": "...",
  "original_filename": "tugas_akhir.pdf",
  "mime_type": "application/pdf"
}
```

---

## 5. Pertimbangan Keamanan (Security Considerations)
1. **Pencegahan Path Traversal**: Nama file asli hanya disimpan sebagai metadata container dan disanitasi menggunakan `werkzeug.utils.secure_filename`; nama tersebut tidak digunakan sebagai path filesystem.
2. **Generic Error Message**: Pesan error kegagalan dekripsi sengaja dibuat generik (*"Dekripsi gagal: password salah atau data telah dimodifikasi."*) agar penyerang tidak dapat membedakan antara password salah dan modifikasi data.
3. **Pembersihan Memori Kunci**: Variabel kunci (`key`) dihapus secara eksplisit setelah operasi enkripsi/dekripsi selesai.
4. **Batas Ukuran Upload**: Dibatasi oleh Flask `MAX_CONTENT_LENGTH` sebesar 64 MB untuk mitigasi Denial of Service (DoS).
