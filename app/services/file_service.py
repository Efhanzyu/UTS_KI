"""Filename sanitization and MIME type helpers for uploaded files."""
import mimetypes
from werkzeug.utils import secure_filename


def get_safe_filename(user_filename: str) -> str:
    """
    Sanitasi nama file dari pengguna menggunakan werkzeug secure_filename.

    HANYA untuk metadata/display, BUKAN untuk digunakan sebagai path filesystem.
    secure_filename menghapus karakter berbahaya seperti '..', '/', dll.

    Args:
        user_filename: Nama file yang diberikan pengguna

    Returns:
        Nama file yang sudah disanitasi, atau "file" jika hasilnya kosong
    """
    sanitized = secure_filename(user_filename)
    return sanitized if sanitized else "file"


def get_mime_type(filename: str) -> str:
    """
    Deteksi MIME type berdasarkan ekstensi file.

    Args:
        filename: Nama file (hanya ekstensinya yang digunakan)

    Returns:
        MIME type string (contoh: "application/pdf")
        Default: "application/octet-stream" untuk tipe tidak dikenal
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"
