"""
Encryption Service — orkestrator proses enkripsi dan dekripsi.

Modul ini menghubungkan:
  - KDF (PBKDF2-HMAC-SHA256) dari kdf.py
  - Algoritma enkripsi (AES-GCM / ChaCha20) dari masing-masing modul
  - Format container .enc dari container.py

Flow enkripsi:
  password + plaintext
    → generate_salt()
    → derive_key(password, salt)
    → generate_nonce()
    → encrypt(key, plaintext, nonce)
    → pack_encrypted_file(...)
    → Base64 (untuk teks) / bytes (untuk file)

Flow dekripsi:
  ciphertext_b64 / .enc bytes
    → unpack_encrypted_file(...)
    → derive_key(password, salt dari header)
    → decrypt(key, ciphertext, nonce dari header)
    → plaintext
"""
from cryptography.exceptions import InvalidTag

from app.crypto import kdf as kdf_module
from app.crypto import aes_gcm
from app.crypto import chacha20
from app.crypto import container as container_module
from app.utils.encoding import safe_b64decode, safe_b64encode
from config import Config

# Nama algoritma yang didukung (harus konsisten dengan container.py)
ALGORITHM_AES: str = "AES-256-GCM"
ALGORITHM_CHACHA: str = "ChaCha20-Poly1305"
KDF_NAME: str = "PBKDF2-HMAC-SHA256"

SUPPORTED_ALGORITHMS: frozenset = frozenset({ALGORITHM_AES, ALGORITHM_CHACHA})


def _get_crypto_module(algorithm: str):
    """
    Kembalikan modul crypto yang sesuai berdasarkan nama algoritma.

    Args:
        algorithm: "AES-256-GCM" atau "ChaCha20-Poly1305"

    Returns:
        Modul aes_gcm atau chacha20

    Raises:
        ValueError: Jika algoritma tidak didukung
    """
    if algorithm == ALGORITHM_AES:
        return aes_gcm
    elif algorithm == ALGORITHM_CHACHA:
        return chacha20
    else:
        raise ValueError(f"Algoritma tidak didukung: '{algorithm}'")


# ── Enkripsi Teks ─────────────────────────────────────────────────

def encrypt_text(plaintext: str, password: str, algorithm: str = ALGORITHM_AES) -> dict:
    """
    Enkripsi plaintext teks menjadi Base64 ciphertext.

    Seluruh metadata (salt, nonce, algorithm) dikemas dalam container
    format dan di-encode ke Base64 untuk kemudahan transmisi teks.

    Args:
        plaintext:  Teks yang akan dienkripsi
        password:   Password pengguna (tidak disimpan)
        algorithm:  Nama algoritma (default: AES-256-GCM)

    Returns:
        Dict berisi:
          - ciphertext_b64: Base64 string siap ditampilkan/disalin
          - algorithm, key_size_bits, kdf, pbkdf2_iterations,
            salt_size_bytes, nonce_size_bytes, ciphertext_size_bytes

    Security:
        Key tidak dikembalikan dan tidak disimpan di mana pun.
        Password tidak disimpan setelah fungsi selesai.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algoritma tidak didukung: '{algorithm}'")

    iterations = Config.PBKDF2_ITERATIONS
    crypto = _get_crypto_module(algorithm)

    # 1. Generate random salt (baru setiap enkripsi)
    salt = kdf_module.generate_salt()

    # 2. Derive key dari password + salt (tidak disimpan)
    key = kdf_module.derive_key(password, salt, iterations)

    # 3. Generate random nonce (baru setiap enkripsi)
    nonce = crypto.generate_nonce()

    # 4. Enkripsi plaintext
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext = crypto.encrypt(key, plaintext_bytes, nonce)

    # 5. Kemas metadata + ciphertext ke format container
    container_bytes = container_module.pack_encrypted_file(
        algorithm=algorithm,
        kdf=KDF_NAME,
        pbkdf2_iterations=iterations,
        salt=salt,
        nonce=nonce,
        ciphertext=ciphertext,
    )

    # 6. Encode seluruh container ke Base64 untuk output teks
    ciphertext_b64 = safe_b64encode(container_bytes)

    # Hapus key dari memory sesegera mungkin (Python GC akan handle)
    del key

    return {
        "ciphertext_b64": ciphertext_b64,
        "algorithm": algorithm,
        "key_size_bits": kdf_module.KEY_SIZE * 8,
        "kdf": KDF_NAME,
        "pbkdf2_iterations": iterations,
        "salt_size_bytes": len(salt),
        "nonce_size_bytes": len(nonce),
        "ciphertext_size_bytes": len(ciphertext),
    }


def decrypt_text(ciphertext_b64: str, password: str) -> str:
    """
    Dekripsi Base64 ciphertext menjadi plaintext.

    Args:
        ciphertext_b64: Base64 string yang dihasilkan oleh encrypt_text()
        password:       Password yang sama dengan saat enkripsi

    Returns:
        Plaintext string asli

    Raises:
        ValueError:                   Base64 tidak valid
        container_module.ContainerError: Container rusak atau tidak valid
        InvalidTag:                   Password salah atau data dimodifikasi
    """
    # Decode Base64 → container bytes
    try:
        container_bytes = safe_b64decode(ciphertext_b64)
    except ValueError as exc:
        raise ValueError("Ciphertext Base64 tidak valid.") from exc

    # Parse container → metadata + ciphertext
    unpacked = container_module.unpack_encrypted_file(container_bytes)

    algorithm = unpacked["algorithm"]
    salt = unpacked["salt"]
    nonce = unpacked["nonce"]
    ciphertext = unpacked["ciphertext"]
    iterations = unpacked["pbkdf2_iterations"]

    crypto = _get_crypto_module(algorithm)

    # Derive key dari password + salt dari container
    key = kdf_module.derive_key(password, salt, iterations)

    # Dekripsi — akan raise InvalidTag jika password salah atau data dimodifikasi
    plaintext_bytes = crypto.decrypt(key, ciphertext, nonce)

    del key  # Bersihkan key dari memory

    return plaintext_bytes.decode("utf-8")


# ── Enkripsi File ─────────────────────────────────────────────────

def encrypt_file(
    file_bytes: bytes,
    password: str,
    algorithm: str,
    original_filename: str = "",
    mime_type: str = "",
) -> bytes:
    """
    Enkripsi file bytes menjadi .enc container bytes.

    Args:
        file_bytes:        Isi file asli sebagai bytes
        password:          Password pengguna
        algorithm:         Nama algoritma enkripsi
        original_filename: Nama file asli (disimpan dalam header .enc)
        mime_type:         MIME type file asli (disimpan dalam header .enc)

    Returns:
        Bytes format .enc siap disimpan ke file atau dikirim ke browser

    Raises:
        ValueError: Algoritma tidak didukung
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algoritma tidak didukung: '{algorithm}'")

    iterations = Config.PBKDF2_ITERATIONS
    crypto = _get_crypto_module(algorithm)

    salt = kdf_module.generate_salt()
    key = kdf_module.derive_key(password, salt, iterations)
    nonce = crypto.generate_nonce()

    ciphertext = crypto.encrypt(key, file_bytes, nonce)
    del key

    container_bytes = container_module.pack_encrypted_file(
        algorithm=algorithm,
        kdf=KDF_NAME,
        pbkdf2_iterations=iterations,
        salt=salt,
        nonce=nonce,
        ciphertext=ciphertext,
        original_filename=original_filename,
        mime_type=mime_type,
    )

    return container_bytes


def decrypt_file(enc_bytes: bytes, password: str) -> dict:
    """
    Dekripsi .enc bytes menjadi file bytes asli.

    Args:
        enc_bytes: Isi file .enc sebagai bytes
        password:  Password yang sama dengan saat enkripsi

    Returns:
        Dict dengan keys:
          - file_bytes (bytes): File asli
          - original_filename (str): Nama file asli dari metadata
          - mime_type (str): MIME type dari metadata
          - algorithm (str): Algoritma yang digunakan

    Raises:
        container_module.ContainerError: Container rusak/tidak valid
        InvalidTag: Password salah atau data dimodifikasi
    """
    unpacked = container_module.unpack_encrypted_file(enc_bytes)

    algorithm = unpacked["algorithm"]
    salt = unpacked["salt"]
    nonce = unpacked["nonce"]
    ciphertext = unpacked["ciphertext"]
    iterations = unpacked["pbkdf2_iterations"]

    crypto = _get_crypto_module(algorithm)
    key = kdf_module.derive_key(password, salt, iterations)

    file_bytes = crypto.decrypt(key, ciphertext, nonce)
    del key

    return {
        "file_bytes": file_bytes,
        "original_filename": unpacked["original_filename"],
        "mime_type": unpacked["mime_type"],
        "algorithm": algorithm,
    }
