"""
Brankas File Tugas Kuliah — Flask Application Factory.

Menggunakan Application Factory Pattern untuk memudahkan testing
dan deployment di berbagai environment.
"""
import os
from flask import Flask, jsonify
from config import Config


def create_app(config_class: type = Config) -> Flask:
    """
    Buat dan konfigurasi instance Flask.

    Args:
        config_class: Kelas konfigurasi (default: Config dari config.py)

    Returns:
        Instance Flask yang sudah dikonfigurasi
    """
    # Tentukan lokasi templates dan static di root project
    # (bukan di dalam folder app/)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, "templates"),
        static_folder=os.path.join(root_dir, "static"),
    )

    app.config.from_object(config_class)

    # ── Register Blueprints ────────────────────────────────────────
    from app.routes.pages import pages_bp
    from app.routes.api import api_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    # ── Error Handlers ─────────────────────────────────────────────
    @app.errorhandler(413)
    def file_too_large(error):
        max_mb = app.config.get("MAX_CONTENT_MB", 64)
        return jsonify({
            "success": False,
            "message": f"File terlalu besar. Maksimal {max_mb} MB."
        }), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "message": "Endpoint tidak ditemukan."}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"success": False, "message": "Method tidak diizinkan."}), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "Terjadi kesalahan internal pada server."
        }), 500

    return app
