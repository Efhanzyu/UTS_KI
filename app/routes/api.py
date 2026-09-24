"""
API routes — JSON endpoints untuk enkripsi, dekripsi, dan benchmark.

Semua response menggunakan format konsisten:
  Sukses: {"success": true, "message": "...", "data": {...}}
  Error:  {"success": false, "message": "..."}

Stack trace TIDAK pernah dikembalikan ke pengguna.
"""
import io
import uuid
from flask import Blueprint, request, jsonify, send_file, session
from cryptography.exceptions import InvalidTag

from app.services import encryption_service
from app.services import file_service
from app.services import benchmark_service
from app.services import benchmark_export_service
from app.services import storage_service
from app.crypto import container as container_module
from app.utils.security import validate_password, validate_algorithm, validate_plaintext

api_bp = Blueprint("api", __name__, url_prefix="/api")
_storage = storage_service.StorageService()

# Pesan error generic untuk kegagalan dekripsi
# Pesan yang sama untuk password salah DAN data dimodifikasi
# (agar attacker tidak bisa membedakan keduanya)
_DECRYPT_FAIL_MSG = "Dekripsi gagal: password salah atau data telah dimodifikasi."


def _storage_owner_id() -> str:
    """Return the signed session owner ID used to scope storage operations."""
    owner_id = session.get("storage_owner_id")
    if not isinstance(owner_id, str) or len(owner_id) != 32:
        owner_id = uuid.uuid4().hex
        session["storage_owner_id"] = owner_id
    return owner_id


def _ok(message: str, data: dict | None = None):
    """Helper: response sukses."""
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    return jsonify(resp)


def _err(message: str, status: int = 400):
    """Helper: response error (tanpa stack trace)."""
    return jsonify({"success": False, "message": message}), status


# ── Health Check ──────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return _ok("Brankas API is running", {"status": "healthy", "app": "Brankas File Tugas Kuliah"})


# ── Enkripsi Teks ─────────────────────────────────────────────────

@api_bp.route("/encrypt/text", methods=["POST"])
def encrypt_text():
    """
    POST /api/encrypt/text

    Body JSON:
        plaintext  (str, wajib)
        password   (str, wajib)
        algorithm  (str, opsional, default: AES-256-GCM)

    Response data:
        ciphertext_b64, algorithm, key_size_bits, kdf,
        pbkdf2_iterations, salt_size_bytes, nonce_size_bytes, ciphertext_size_bytes
    """
    data = request.get_json(silent=True)
    if not data:
        return _err("Request body JSON tidak valid.")

    plaintext = data.get("plaintext", "")
    password = data.get("password", "")
    algorithm = data.get("algorithm", "AES-256-GCM").strip()

    # Validasi input
    ok, msg = validate_plaintext(plaintext)
    if not ok:
        return _err(msg)
    ok, msg = validate_password(password)
    if not ok:
        return _err(msg)
    ok, msg = validate_algorithm(algorithm)
    if not ok:
        return _err(msg)

    try:
        result = encryption_service.encrypt_text(plaintext, password, algorithm)
        return _ok("Enkripsi berhasil.", result)
    except ValueError as exc:
        return _err(str(exc))
    except Exception:
        # Jangan expose detail error ke pengguna
        return _err("Enkripsi gagal karena kesalahan internal.", 500)


# ── Dekripsi Teks ─────────────────────────────────────────────────

@api_bp.route("/decrypt/text", methods=["POST"])
def decrypt_text():
    """
    POST /api/decrypt/text

    Body JSON:
        ciphertext_b64 (str, wajib)
        password       (str, wajib)

    Response data:
        plaintext
    """
    data = request.get_json(silent=True)
    if not data:
        return _err("Request body JSON tidak valid.")

    ciphertext_b64 = data.get("ciphertext_b64", "").strip()
    password = data.get("password", "")

    if not ciphertext_b64:
        return _err("Ciphertext tidak boleh kosong.")
    ok, msg = validate_password(password)
    if not ok:
        return _err(msg)

    try:
        plaintext = encryption_service.decrypt_text(ciphertext_b64, password)
        return _ok("Dekripsi berhasil.", {"plaintext": plaintext})
    except (
        InvalidTag,
        ValueError,
        container_module.ContainerError,
    ):
        # Pesan generic — jangan bedakan password salah vs data dimodifikasi
        return _err(_DECRYPT_FAIL_MSG)
    except Exception:
        return _err(_DECRYPT_FAIL_MSG)


# ── Enkripsi File ─────────────────────────────────────────────────

@api_bp.route("/encrypt/file", methods=["POST"])
def encrypt_file():
    """
    POST /api/encrypt/file  (multipart/form-data)

    Form fields:
        file      (file, wajib)
        password  (str, wajib)
        algorithm (str, opsional, default: AES-256-GCM)

    Response:
        File download dengan nama <original_name>.enc
    """
    if "file" not in request.files:
        return _err("File tidak ditemukan dalam request.")

    uploaded_file = request.files["file"]
    password = request.form.get("password", "")
    algorithm = request.form.get("algorithm", "AES-256-GCM").strip()

    if not uploaded_file or uploaded_file.filename == "":
        return _err("File tidak dipilih.")
    ok, msg = validate_password(password)
    if not ok:
        return _err(msg)
    ok, msg = validate_algorithm(algorithm)
    if not ok:
        return _err(msg)

    try:
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return _err("File kosong tidak dapat dienkripsi.")

        # Sanitasi nama file (hanya untuk metadata, BUKAN untuk path)
        safe_name = file_service.get_safe_filename(uploaded_file.filename)
        mime_type = file_service.get_mime_type(safe_name)

        enc_bytes = encryption_service.encrypt_file(
            file_bytes=file_bytes,
            password=password,
            algorithm=algorithm,
            original_filename=safe_name,
            mime_type=mime_type,
        )

        output_name = safe_name + ".enc"

        stored_file_id = None
        if _storage.is_configured():
            stored_file_id = uuid.uuid4().hex
            storage_path = _storage.build_path(_storage_owner_id(), stored_file_id)
            try:
                _storage.upload(storage_path, enc_bytes, "application/octet-stream")
            except storage_service.StorageError:
                return _err("File terenkripsi gagal disimpan. Silakan coba lagi.", 502)

        response = send_file(
            io.BytesIO(enc_bytes),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=output_name,
        )
        if stored_file_id:
            response.headers["X-Brankas-Storage-Id"] = stored_file_id
        return response

    except ValueError as exc:
        return _err(str(exc))
    except Exception:
        return _err("Enkripsi file gagal karena kesalahan internal.", 500)


# ── Dekripsi File ─────────────────────────────────────────────────

@api_bp.route("/decrypt/file", methods=["POST"])
def decrypt_file():
    """
    POST /api/decrypt/file  (multipart/form-data)

    Form fields:
        file      (file .enc, wajib)
        password  (str, wajib)

    Response:
        File download dengan nama file asli
    """
    if "file" not in request.files:
        return _err("File tidak ditemukan dalam request.")

    uploaded_file = request.files["file"]
    password = request.form.get("password", "")

    if not uploaded_file or uploaded_file.filename == "":
        return _err("File tidak dipilih.")
    ok, msg = validate_password(password)
    if not ok:
        return _err(msg)

    try:
        enc_bytes = uploaded_file.read()
        if not enc_bytes:
            return _err("File kosong.")

        result = encryption_service.decrypt_file(enc_bytes, password)

        file_bytes = result["file_bytes"]
        original_filename = result["original_filename"] or "decrypted_file"
        mime_type = result["mime_type"] or "application/octet-stream"

        # Sanitasi nama file output (defensive)
        safe_output_name = file_service.get_safe_filename(original_filename)
        if not safe_output_name:
            safe_output_name = "decrypted_file"

        return send_file(
            io.BytesIO(file_bytes),
            mimetype=mime_type,
            as_attachment=True,
            download_name=safe_output_name,
        )

    except (
        InvalidTag,
        container_module.MagicError,
        container_module.VersionError,
        container_module.MetadataError,
        container_module.AlgorithmError,
        container_module.ContainerError,
    ):
        return _err(_DECRYPT_FAIL_MSG)
    except Exception:
        return _err(_DECRYPT_FAIL_MSG)


# ── Supabase Storage ─────────────────────────────────────────────

@api_bp.route("/storage/files", methods=["GET"])
def list_stored_files():
    """List encrypted files belonging to the current browser session."""
    if not _storage.is_configured():
        return _ok("Supabase Storage belum dikonfigurasi.", {"configured": False, "files": []})

    try:
        owner_id = _storage_owner_id()
        objects = _storage.list(owner_id)
        files = []
        for obj in objects:
            name = obj.get("name", "") if isinstance(obj, dict) else ""
            if not name.endswith(".enc"):
                continue
            file_id = name[:-4]
            try:
                path = _storage.build_path(owner_id, file_id)
                encrypted_bytes = _storage.download(path)
                metadata = container_module.unpack_encrypted_file(encrypted_bytes)
            except (storage_service.StorageError, container_module.ContainerError):
                continue
            files.append({
                "id": file_id,
                "original_filename": file_service.get_safe_filename(
                    metadata.get("original_filename") or "encrypted_file"
                ),
                "algorithm": metadata["algorithm"],
                "size_bytes": len(encrypted_bytes),
                "created_at": obj.get("created_at") if isinstance(obj, dict) else None,
            })
        return _ok("Daftar file berhasil dimuat.", {"configured": True, "files": files})
    except storage_service.StorageError:
        return _err("Daftar file tersimpan tidak dapat dimuat.", 502)


@api_bp.route("/storage/files/<file_id>", methods=["GET"])
def download_stored_file(file_id: str):
    """Download an encrypted object owned by the current browser session."""
    if not _storage.is_configured():
        return _err("Supabase Storage belum dikonfigurasi.", 503)
    try:
        owner_id = _storage_owner_id()
        path = _storage.build_path(owner_id, file_id)
        encrypted_bytes = _storage.download(path)
        metadata = container_module.unpack_encrypted_file(encrypted_bytes)
        filename = file_service.get_safe_filename(
            metadata.get("original_filename") or "encrypted_file"
        ) + ".enc"
        return send_file(
            io.BytesIO(encrypted_bytes),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=filename,
        )
    except (storage_service.StorageError, container_module.ContainerError):
        return _err("File terenkripsi tidak ditemukan.", 404)


@api_bp.route("/storage/files/<file_id>/decrypt", methods=["POST"])
def decrypt_stored_file(file_id: str):
    """Decrypt an owned encrypted object without persisting plaintext."""
    if not _storage.is_configured():
        return _err("Supabase Storage belum dikonfigurasi.", 503)
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    ok, msg = validate_password(password)
    if not ok:
        return _err(msg)
    try:
        path = _storage.build_path(_storage_owner_id(), file_id)
        result = encryption_service.decrypt_file(_storage.download(path), password)
        filename = file_service.get_safe_filename(result.get("original_filename") or "decrypted_file")
        return send_file(
            io.BytesIO(result["file_bytes"]),
            mimetype=result.get("mime_type") or "application/octet-stream",
            as_attachment=True,
            download_name=filename,
        )
    except (
        storage_service.StorageError,
        InvalidTag,
        container_module.MagicError,
        container_module.VersionError,
        container_module.MetadataError,
        container_module.AlgorithmError,
        container_module.ContainerError,
    ):
        return _err(_DECRYPT_FAIL_MSG)
    except Exception:
        return _err(_DECRYPT_FAIL_MSG)


@api_bp.route("/storage/files/<file_id>", methods=["DELETE"])
def delete_stored_file(file_id: str):
    """Delete an encrypted object owned by the current browser session."""
    if not _storage.is_configured():
        return _err("Supabase Storage belum dikonfigurasi.", 503)
    try:
        path = _storage.build_path(_storage_owner_id(), file_id)
        _storage.remove(path)
        return _ok("File terenkripsi berhasil dihapus.")
    except storage_service.StorageError:
        return _err("File terenkripsi gagal dihapus.", 502)


# ── Benchmark ─────────────────────────────────────────────────────

@api_bp.route("/benchmark", methods=["POST"])
def run_benchmark():
    data=request.get_json(silent=True) or {}
    if not isinstance(data,dict): return _err("Request body JSON tidak valid.")
    raw_runs=data.get("runs",benchmark_service.Config.BENCHMARK_RUNS)
    if type(raw_runs) is int:
        runs = raw_runs
    elif isinstance(raw_runs, str) and raw_runs.isdecimal():
        runs = int(raw_runs)
    else:
        return _err("runs harus berupa bilangan bulat antara 1 dan 100.")
    if not 1<=runs<=benchmark_service.Config.BENCHMARK_MAX_RUNS: return _err("runs harus berada antara 1 dan 100.")
    size_arg=data.get("size")
    if size_arg is not None:
        mapping={"1kb":1,"1mb":1024,"10mb":10240}; key=str(size_arg).lower().replace(" ","")
        if key not in mapping: return _err("size harus berupa 1 KB, 1 MB, atau 10 MB.")
        sizes=[mapping[key]]
    else:
        sizes=data.get("sizes_kb",[1,1024,10240])
        if not isinstance(sizes,list): return _err("sizes_kb harus berupa daftar ukuran dalam KB.")
        sizes=[s for s in sizes if type(s) is int and 1<=s<=20480]
        if not sizes: return _err("Pilih ukuran benchmark antara 1 KB dan 20 MB.")
    try: return _ok("Benchmark selesai.",benchmark_service.run_full_benchmark(sizes,runs))
    except ValueError as exc: return _err(str(exc))
    except Exception: return _err("Benchmark gagal karena kesalahan internal.",500)


def _benchmark_export(format_name):
    data = request.get_json(silent=True) or {}
    try:
        if format_name == "csv":
            payload = benchmark_export_service.csv_bytes(data)
            return send_file(io.BytesIO(payload), as_attachment=True,
                             download_name="benchmark-results.csv", mimetype="text/csv")
        payload = benchmark_export_service.xlsx_bytes(data)
        return send_file(
            io.BytesIO(payload), as_attachment=True,
            download_name="benchmark-results.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ValueError as exc:
        return _err(str(exc))
    except Exception:
        return _err("Export benchmark gagal. Silakan coba lagi.", 500)


@api_bp.route("/benchmark/export/csv", methods=["POST"])
def export_benchmark_csv():
    return _benchmark_export("csv")


@api_bp.route("/benchmark/export/excel", methods=["POST"])
def export_benchmark_excel():
    return _benchmark_export("excel")
