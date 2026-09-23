"""
Entry point aplikasi Brankas File Tugas Kuliah.

Cara menjalankan:
    python app.py

Atau dengan Flask CLI:
    flask run

Aplikasi berjalan di: http://127.0.0.1:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug mode dikontrol via FLASK_ENV di .env
    # Jangan aktifkan debug=True secara manual di production!
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
    )
