"""
Format file .enc — BRANKAS Container.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT BINARY:

  Offset  Size  Isi
  ──────  ────  ──────────────────────────────────────
  0       8     MAGIC = b"BRANKAS\\x01"
  8       2     VERSION = b"\\x00\\x01" (big-endian uint16)
  10      4     HEADER_LEN (big-endian uint32)
  14      N     HEADER (JSON UTF-8, panjang = HEADER_LEN)
  14+N    ∞     CIPHERTEXT (termasuk AEAD auth tag 16 byte)

HEADER adalah JSON yang berisi:
  {
    "version": "1",
    "algorithm": "AES-256-GCM",       ← nama algoritma
    "kdf": "PBKDF2-HMAC-SHA256",       ← nama KDF
    "pbkdf2_iterations": 600000,       ← iterasi KDF
    "salt_b64": "...",                 ← salt (Base64)
    "nonce_b64": "...",                ← nonce (Base64)
    "original_filename": "report.pdf", ← nama file asli
    "mime_type": "application/pdf"     ← tipe MIME
  }

YANG TIDAK DISIMPAN DI CONTAINER:
  - Password
  - Encryption key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import struct
from typing import Dict, Any

from app.utils.encoding import safe_b64decode, safe_b64encode

# ── Konstanta Format ──────────────────────────────────────────────
# Magic bytes: identifikasi unik format file ini
MAGIC: bytes = b"BRANKAS\x01"
MAGIC_SIZE: int = 8

# Versi format container (big-endian uint16)
VERSION: bytes = b"\x00\x01"
VERSION_SIZE: int = 2

# Ukuran field panjang header (big-endian uint32)
HEADER_LEN_SIZE: int = 4

# Set versi yang didukung untuk validasi
SUPPORTED_VERSIONS: frozenset = frozenset({b"\x00\x01"})

# Set algoritma yang didukung
SUPPORTED_ALGORITHMS: frozenset = frozenset({"AES-256-GCM", "ChaCha20-Poly1305"})

# Ukuran minimum file .enc yang valid (magic + version + header_len + 1 char)
MIN_FILE_SIZE: int = MAGIC_SIZE + VERSION_SIZE + HEADER_LEN_SIZE + 1


# ── Custom Exceptions ─────────────────────────────────────────────

class ContainerError(Exception):
    """Base exception untuk error parsing container .enc."""
    pass


class MagicError(ContainerError):
    """Magic number tidak valid — bukan file .enc dari aplikasi ini."""
    pass


class VersionError(ContainerError):
    """Versi container tidak didukung."""
    pass


class MetadataError(ContainerError):
    """Metadata container rusak atau tidak lengkap."""
    pass


class AlgorithmError(ContainerError):
    """Algoritma dalam container tidak dikenal atau tidak didukung."""
    pass


# ── Pack (Buat .enc) ──────────────────────────────────────────────

def pack_encrypted_file(
    algorithm: str,
    kdf: str,
    pbkdf2_iterations: int,
    salt: bytes,
    nonce: bytes,
    ciphertext: bytes,
    original_filename: str = "",
    mime_type: str = "",
) -> bytes:
    """
    Buat binary .enc dari komponen enkripsi.

    Args:
        algorithm:          Nama algoritma ("AES-256-GCM" atau "ChaCha20-Poly1305")
        kdf:                Nama KDF ("PBKDF2-HMAC-SHA256")
        pbkdf2_iterations:  Jumlah iterasi PBKDF2
        salt:               Salt bytes (akan di-encode Base64 dalam header)
        nonce:              Nonce bytes (akan di-encode Base64 dalam header)
        ciphertext:         Ciphertext bytes termasuk authentication tag
        original_filename:  Nama file asli (untuk metadata, opsional)
        mime_type:          MIME type file asli (opsional)

    Returns:
        Binary data format .enc siap disimpan ke file

    Raises:
        AlgorithmError: Jika algoritma tidak didukung
        MetadataError:  Jika ciphertext kosong
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise AlgorithmError(f"Algoritma tidak didukung: {algorithm}")
    if not ciphertext:
        raise MetadataError("Ciphertext tidak boleh kosong.")

    # Header JSON — salt dan nonce di-encode Base64 agar JSON-compatible
    header: Dict[str, Any] = {
        "version": "1",
        "algorithm": algorithm,
        "kdf": kdf,
        "pbkdf2_iterations": pbkdf2_iterations,
        "salt_b64": safe_b64encode(salt),
        "nonce_b64": safe_b64encode(nonce),
        "original_filename": original_filename,
        "mime_type": mime_type,
    }

    # Serialisasi JSON (compact, tanpa spasi ekstra)
    header_bytes: bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")

    # Panjang header sebagai uint32 big-endian
    header_len_bytes: bytes = struct.pack(">I", len(header_bytes))

    # Gabungkan semua komponen
    return MAGIC + VERSION + header_len_bytes + header_bytes + ciphertext


# ── Unpack (Parse .enc) ───────────────────────────────────────────

def unpack_encrypted_file(data: bytes) -> Dict[str, Any]:
    """
    Parse binary .enc dan kembalikan seluruh metadata + ciphertext.

    Args:
        data: Isi file .enc sebagai bytes

    Returns:
        Dict dengan keys:
            algorithm, kdf, pbkdf2_iterations, salt (bytes),
            nonce (bytes), original_filename, mime_type, ciphertext (bytes)

    Raises:
        MagicError:     File bukan format .enc yang valid
        VersionError:   Versi container tidak didukung
        MetadataError:  Header JSON rusak atau tidak lengkap
        AlgorithmError: Algoritma tidak dikenal
    """
    # Validasi ukuran minimum
    if len(data) < MIN_FILE_SIZE:
        raise MetadataError("File terlalu kecil untuk format .enc yang valid.")

    # ── Parse Magic ───────────────────────────────────────────────
    magic = data[:MAGIC_SIZE]
    if magic != MAGIC:
        raise MagicError(
            "Magic number tidak valid. "
            "File ini bukan file .enc yang dihasilkan aplikasi Brankas."
        )

    # ── Parse Version ─────────────────────────────────────────────
    offset = MAGIC_SIZE
    version = data[offset : offset + VERSION_SIZE]
    if version not in SUPPORTED_VERSIONS:
        raise VersionError(
            f"Versi container tidak didukung: {version.hex()}. "
            f"Versi yang didukung: {', '.join(v.hex() for v in SUPPORTED_VERSIONS)}"
        )
    offset += VERSION_SIZE

    # ── Parse Header Length ───────────────────────────────────────
    header_len = struct.unpack(">I", data[offset : offset + HEADER_LEN_SIZE])[0]
    offset += HEADER_LEN_SIZE

    if offset + header_len > len(data):
        raise MetadataError(
            "Header length dalam file melebihi ukuran total file. "
            "File mungkin rusak."
        )

    # ── Parse Header JSON ─────────────────────────────────────────
    header_bytes = data[offset : offset + header_len]
    try:
        header: Dict[str, Any] = json.loads(header_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MetadataError(f"Header JSON tidak valid atau rusak: {exc}") from exc
    offset += header_len

    # ── Validasi Field Wajib ──────────────────────────────────────
    required_fields = ["algorithm", "kdf", "pbkdf2_iterations", "salt_b64", "nonce_b64"]
    for field in required_fields:
        if field not in header:
            raise MetadataError(
                f"Header tidak lengkap: field '{field}' tidak ditemukan."
            )

    # ── Validasi Algoritma ────────────────────────────────────────
    algorithm: str = header["algorithm"]
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise AlgorithmError(
            f"Algoritma tidak dikenal dalam container: '{algorithm}'. "
            f"Didukung: {', '.join(SUPPORTED_ALGORITHMS)}"
        )

    # ── Decode Salt dan Nonce dari Base64 ─────────────────────────
    try:
        salt: bytes = safe_b64decode(header["salt_b64"])
        nonce: bytes = safe_b64decode(header["nonce_b64"])
    except ValueError as exc:
        raise MetadataError(
            f"Gagal mendekode Base64 untuk salt/nonce: {exc}"
        ) from exc

    # ── Validasi ukuran salt dan nonce tidak kosong ───────────────
    if not salt:
        raise MetadataError("Salt dalam container kosong.")
    if not nonce:
        raise MetadataError("Nonce dalam container kosong.")

    # ── Ambil Ciphertext ──────────────────────────────────────────
    ciphertext: bytes = data[offset:]
    if not ciphertext:
        raise MetadataError("Ciphertext kosong dalam container.")

    # ── Validasi tipe data pbkdf2_iterations ─────────────────────
    try:
        iterations = int(header["pbkdf2_iterations"])
        if iterations <= 0:
            raise ValueError("Iterations harus positif")
    except (ValueError, TypeError) as exc:
        raise MetadataError(f"pbkdf2_iterations tidak valid: {exc}") from exc

    return {
        "algorithm": algorithm,
        "kdf": header["kdf"],
        "pbkdf2_iterations": iterations,
        "salt": salt,
        "nonce": nonce,
        "original_filename": header.get("original_filename", ""),
        "mime_type": header.get("mime_type", ""),
        "ciphertext": ciphertext,
    }
