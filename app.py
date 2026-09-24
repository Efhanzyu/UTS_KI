"""
Entry point aplikasi Brankas File Tugas Kuliah.

Cara menjalankan:
    python app.py

Atau dengan Flask CLI:
    flask run

Aplikasi berjalan di: http://127.0.0.1:5000
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Development server only; Render uses Gunicorn via render.yaml.
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config["DEBUG"],
    )
