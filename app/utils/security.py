"""
Security utilities — validasi input dan keamanan request.
"""

MAX_PASSWORD_LENGTH: int = 256
MAX_PLAINTEXT_LENGTH: int = 10 * 1024 * 1024  # 10 MB untuk enkripsi teks

VALID_ALGORITHMS: frozenset = frozenset({"AES-256-GCM", "ChaCha20-Poly1305"})


def validate_password(password: str) -> tuple[bool, str | None]:
    """
    Validasi password dari input pengguna.

    Returns:
        (True, None) jika valid
        (False, pesan_error) jika tidak valid
    """
    if not password:
        return False, "Password tidak boleh kosong."
    if not isinstance(password, str):
        return False, "Password harus berupa string."
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password terlalu panjang (maksimal {MAX_PASSWORD_LENGTH} karakter)."
    return True, None


def validate_algorithm(algorithm: str) -> tuple[bool, str | None]:
    """
    Validasi nama algoritma.

    Returns:
        (True, None) jika valid
        (False, pesan_error) jika tidak valid
    """
    if not algorithm:
        return False, "Algoritma tidak boleh kosong."
    if algorithm not in VALID_ALGORITHMS:
        valid_list = ", ".join(sorted(VALID_ALGORITHMS))
        return False, f"Algoritma tidak didukung. Pilih: {valid_list}"
    return True, None


def validate_plaintext(plaintext: str) -> tuple[bool, str | None]:
    """Validasi plaintext untuk enkripsi teks."""
    if not isinstance(plaintext, str):
        return False, "Plaintext harus berupa teks."
    if plaintext == "":
        return False, "Plaintext tidak boleh kosong."
    if len(plaintext.encode("utf-8")) > MAX_PLAINTEXT_LENGTH:
        return False, f"Plaintext terlalu besar (maksimal {MAX_PLAINTEXT_LENGTH // (1024*1024)} MB)."
    return True, None
