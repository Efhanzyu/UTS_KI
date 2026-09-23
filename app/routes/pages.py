"""
Page routes — render HTML templates for Brankas File Tugas Kuliah.
"""
from flask import Blueprint, render_template, request

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    """Halaman beranda / dashboard utilitas."""
    return render_template("index.html", active_page="dashboard")


@pages_bp.route("/encrypt")
@pages_bp.route("/file")
def file_page():
    """Halaman enkripsi file (default) atau dekripsi file."""
    mode = request.args.get("mode", "encrypt")
    return render_template("file.html", active_page="file", initial_mode=mode)


@pages_bp.route("/decrypt")
def decrypt_page():
    """Akses langsung ke halaman dekripsi file."""
    return render_template("file.html", active_page="decrypt", initial_mode="decrypt")


@pages_bp.route("/text")
def text():
    """Halaman enkripsi dan dekripsi teks."""
    return render_template("text.html", active_page="text")


@pages_bp.route("/benchmark")
def benchmark():
    """Halaman benchmark dan analisis kriptografi."""
    return render_template("benchmark.html", active_page="benchmark")
