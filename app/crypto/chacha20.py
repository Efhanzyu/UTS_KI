"""
Enkripsi dan dekripsi menggunakan ChaCha20-Poly1305.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KONSEP PENTING (untuk presentasi):

ChaCha20-Poly1305 adalah algoritma AEAD alternatif:

ChaCha20:
- Stream cipher yang dikembangkan Daniel J. Bernstein (2008)
- Digunakan sebagai komponen enkripsi
- Lebih cepat dari AES pada hardware TANPA AES instruction set
  (contoh: perangkat mobile/embedded tanpa AES-NI)

Poly1305:
- MAC (Message Authentication Code) untuk integrity
- Memastikan ciphertext tidak dimodifikasi

Standar yang digunakan: IETF ChaCha20-Poly1305 (RFC 8439)
- Nonce: 12 byte (96 bit)
- Key: 32 byte (256 bit)
- Authentication tag: 16 byte

Digunakan di: TLS 1.3, WireGuard VPN, Signal Protocol, SSH

Perbandingan dengan AES-GCM:
- ChaCha20: Lebih cepat tanpa AES-NI hardware
- AES-GCM:  Lebih cepat dengan AES-NI (modern PC/server)
- Keduanya: Level keamanan yang setara (256-bit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

# Nonce 12 byte (96 bit) — IETF ChaCha20-Poly1305 (RFC 8439)
NONCE_SIZE: int = 12


def generate_nonce() -> bytes:
    """
    Generate nonce acak 12 byte menggunakan CSPRNG.

    Returns:
        12 byte nonce acak
    """
    return os.urandom(NONCE_SIZE)


def encrypt(key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
    """
    Enkripsi data menggunakan ChaCha20-Poly1305.

    Args:
        key:       32-byte key yang dihasilkan oleh PBKDF2
        plaintext: Data asli yang akan dienkripsi (bytes)
        nonce:     12-byte nonce acak (harus unik per enkripsi)

    Returns:
        Ciphertext + Poly1305 authentication tag (16 byte).
        Total panjang = len(plaintext) + 16 byte

    Notes:
        Library secara otomatis menambahkan authentication tag 16 byte
        di akhir output enkripsi.
    """
    chacha = ChaCha20Poly1305(key)
    ciphertext_with_tag = chacha.encrypt(nonce, plaintext, associated_data=None)
    return ciphertext_with_tag


def decrypt(key: bytes, ciphertext_with_tag: bytes, nonce: bytes) -> bytes:
    """
    Dekripsi data menggunakan ChaCha20-Poly1305.

    Args:
        key:                 32-byte key (harus sama persis dengan key enkripsi)
        ciphertext_with_tag: Ciphertext + authentication tag
        nonce:               12-byte nonce (harus sama persis dengan nonce enkripsi)

    Returns:
        Plaintext asli jika autentikasi berhasil

    Raises:
        cryptography.exceptions.InvalidTag:
            Jika key salah atau ciphertext telah dimodifikasi.
    """
    chacha = ChaCha20Poly1305(key)
    plaintext = chacha.decrypt(nonce, ciphertext_with_tag, associated_data=None)
    return plaintext
