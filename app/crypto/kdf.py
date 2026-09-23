"""
Key Derivation Function menggunakan PBKDF2-HMAC-SHA256.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KONSEP PENTING (untuk presentasi):

PBKDF2 (Password-Based Key Derivation Function 2)
mengubah password pengguna menjadi kunci kriptografi
dengan cara:
  1. Menggabungkan password dengan salt acak
  2. Menjalankan HMAC-SHA256 sebanyak N iterasi
  3. Menghasilkan key 32 byte (256 bit)

Mengapa tidak langsung gunakan password sebagai key?
- Password biasanya pendek dan mudah ditebak
- PBKDF2 + salt memastikan key yang dihasilkan:
  * Selalu 32 byte meski password pendek/panjang
  * Berbeda meski password sama (karena salt berbeda)
  * Sangat mahal di-brute-force karena banyak iterasi

Salt: data acak yang digabung ke password sebelum hashing.
Bukan rahasia, disimpan bersama ciphertext.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Ukuran salt: 32 byte (256 bit)
SALT_SIZE: int = 32

# Ukuran key output: 32 byte (256 bit) — sesuai AES-256
KEY_SIZE: int = 32


def generate_salt() -> bytes:
    """
    Generate salt acak 32 byte menggunakan CSPRNG (os.urandom).

    os.urandom menggunakan sumber entropy sistem operasi
    yang kriptografis aman. JANGAN gunakan random.random() sebagai gantinya.

    Returns:
        32 byte salt acak
    """
    return os.urandom(SALT_SIZE)


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    """
    Turunkan 32-byte encryption key dari password menggunakan PBKDF2-HMAC-SHA256.

    Args:
        password: Password pengguna dalam bentuk string
                  (tidak disimpan setelah fungsi selesai)
        salt:     Random salt 32 byte (bukan rahasia, disimpan bersama ciphertext)
        iterations: Jumlah iterasi PBKDF2 (default dari Config: 600.000)

    Returns:
        Key 32 byte (256 bit) siap digunakan untuk AES-256 atau ChaCha20

    SECURITY NOTES:
        - Key yang dikembalikan TIDAK BOLEH disimpan ke file, database, atau log
        - Salt BOLEH disimpan bersama ciphertext (bukan rahasia)
        - Password di-encode ke UTF-8 bytes hanya untuk durasi proses ini
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=iterations,
    )
    # Encode password ke bytes — hanya digunakan sementara di sini
    key = kdf.derive(password.encode("utf-8"))
    return key
