"""
Enkripsi dan dekripsi menggunakan AES-256-GCM.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KONSEP PENTING (untuk presentasi):

AES-GCM (Galois/Counter Mode) adalah mode AEAD
(Authenticated Encryption with Associated Data):

1. CONFIDENTIALITY: AES-CTR mengenkripsi data
   → ciphertext tidak bisa dibaca tanpa key

2. INTEGRITY: Galois MAC menghasilkan authentication tag
   → tag ini memverifikasi bahwa ciphertext tidak dimodifikasi

3. AUTHENTICITY: Dekripsi gagal jika tag tidak cocok
   → ciphertext yang dimodifikasi satu byte pun akan ditolak

Nonce (Number Used Once):
- 12 byte acak, harus UNIK untuk setiap enkripsi
- Bukan rahasia, disimpan bersama ciphertext
- JANGAN gunakan nonce yang sama dua kali dengan key yang sama
  → ini dapat membocorkan plaintext!

Authentication Tag:
- 16 byte, di-append ke ciphertext oleh library
- Secara otomatis diverifikasi saat dekripsi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Nonce 12 byte (96 bit) — rekomendasi NIST untuk AES-GCM
NONCE_SIZE: int = 12


def generate_nonce() -> bytes:
    """
    Generate nonce acak 12 byte menggunakan CSPRNG.

    Nonce harus unik setiap kali enkripsi dilakukan
    dengan key yang sama. Menggunakan os.urandom memastikan
    probabilitas collision yang sangat kecil.

    Returns:
        12 byte nonce acak
    """
    return os.urandom(NONCE_SIZE)


def encrypt(key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
    """
    Enkripsi data menggunakan AES-256-GCM.

    Args:
        key:       32-byte key yang dihasilkan oleh PBKDF2
        plaintext: Data asli yang akan dienkripsi (bytes)
        nonce:     12-byte nonce acak (harus unik per enkripsi)

    Returns:
        Ciphertext + authentication tag (16 byte) yang digabung oleh library.
        Total panjang = len(plaintext) + 16 byte

    Notes:
        - AESGCM dari library `cryptography` sudah tervalidasi keamanannya
        - Jangan pernah menggunakan nonce yang sama dengan key yang sama
        - Authentication tag secara otomatis disertakan di akhir output
    """
    aesgcm = AESGCM(key)
    # Library otomatis menambahkan authentication tag 16 byte di akhir ciphertext
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return ciphertext_with_tag


def decrypt(key: bytes, ciphertext_with_tag: bytes, nonce: bytes) -> bytes:
    """
    Dekripsi data menggunakan AES-256-GCM.

    Args:
        key:                 32-byte key (harus sama persis dengan key enkripsi)
        ciphertext_with_tag: Ciphertext + authentication tag (output dari encrypt())
        nonce:               12-byte nonce (harus sama persis dengan nonce enkripsi)

    Returns:
        Plaintext asli jika autentikasi berhasil

    Raises:
        cryptography.exceptions.InvalidTag:
            Jika key salah, nonce salah, atau ciphertext telah dimodifikasi.
            Ini membuktikan integritas data.

    Notes:
        Library memverifikasi authentication tag SEBELUM mendekripsi.
        Jika tag tidak cocok, InvalidTag di-raise dan plaintext tidak dikembalikan.
    """
    aesgcm = AESGCM(key)
    # InvalidTag akan di-raise jika password salah atau data dimodifikasi
    plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data=None)
    return plaintext
