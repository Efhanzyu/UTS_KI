"""
File Service — operasi file yang aman.

Prinsip keamanan yang diterapkan:
  1. Nama file dari pengguna TIDAK pernah digunakan sebagai path filesystem
  2. File sementara menggunakan nama UUID acak
  3. File sementara diisolasi di direktori temp OS
  4. Cleanup dilakukan setelah file tidak diperlukan
  5. Path traversal dicegah dengan validasi realpath
"""
import os
import uuid
import mimetypes
import tempfile
from werkzeug.utils import secure_filename

# Direktori temp yang digunakan (diinisialisasi sekali)
_TEMP_DIR: str | None = None


def get_temp_dir() -> str:
    """
    Dapatkan atau buat direktori temp khusus aplikasi.

    Menggunakan tempfile.mkdtemp() untuk membuat direktori
    dengan permission yang aman di OS temp directory.

    Returns:
        Path absolut ke direktori temp
    """
    global _TEMP_DIR
    if _TEMP_DIR is None or not os.path.exists(_TEMP_DIR):
        _TEMP_DIR = tempfile.mkdtemp(prefix="brankas_")
    return _TEMP_DIR


def save_temp_file(data: bytes, suffix: str = ".tmp") -> str:
    """
    Simpan data ke file sementara dengan nama UUID acak.

    JANGAN menggunakan nama file dari pengguna sebagai path.
    UUID acak memastikan tidak ada konflik nama dan tidak ada
    kemungkinan path traversal.

    Args:
        data:   Bytes yang akan disimpan
        suffix: Ekstensi file (contoh: ".enc", ".tmp")

    Returns:
        Path absolut ke file sementara

    Raises:
        OSError: Jika gagal membuat file (misalnya disk penuh)
    """
    temp_dir = get_temp_dir()

    # Nama file = UUID acak (BUKAN nama dari pengguna!)
    safe_name = str(uuid.uuid4()) + suffix
    filepath = os.path.join(temp_dir, safe_name)

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


def cleanup_temp_file(filepath: str) -> None:
    """
    Hapus file sementara dengan validasi keamanan.

    Memverifikasi bahwa path berada dalam direktori temp
    yang diizinkan untuk mencegah penghapusan file sistem.

    Args:
        filepath: Path file yang akan dihapus
    """
    if not filepath:
        return
    try:
        if os.path.exists(filepath):
            # Verifikasi: file harus berada di dalam temp directory kita
            # (anti path traversal attack)
            temp_dir = get_temp_dir()
            real_filepath = os.path.realpath(filepath)
            real_temp_dir = os.path.realpath(temp_dir)

            if real_filepath.startswith(real_temp_dir + os.sep):
                os.remove(filepath)
    except (OSError, PermissionError):
        # Gagal cleanup tidak menyebabkan crash app
        # File akan dibersihkan saat restart OS
        pass


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
