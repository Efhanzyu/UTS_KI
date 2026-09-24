"""Tests for in-memory benchmark downloads."""
import csv
import io

import openpyxl


_ROW = {
    "algorithm": "AES-256-GCM",
    "size_label": "1 KB",
    "avg_encryption_ms": 0.251,
    "avg_decryption_ms": 0.004,
    "min_encryption_ms": 0.004,
    "min_decryption_ms": 0.003,
    "max_encryption_ms": 2.477,
    "max_decryption_ms": 0.012,
}


def test_benchmark_csv_export_uses_attachment_and_valid_csv(client):
    response = client.post("/api/benchmark/export/csv", json={"time_benchmark": [_ROW]})

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "benchmark-results.csv" in response.headers["Content-Disposition"]
    rows = list(csv.reader(io.StringIO(response.data.decode("utf-8-sig"))))
    assert rows[0] == [
        "Algoritma", "Ukuran Data", "Rata-rata Enkripsi (ms)",
        "Rata-rata Dekripsi (ms)", "Min Enkripsi", "Min Dekripsi",
        "Max Enkripsi", "Max Dekripsi",
    ]
    assert rows[1][0:2] == ["AES-256-GCM", "1 KB"]


def test_benchmark_excel_export_is_real_workbook(client):
    response = client.post("/api/benchmark/export/excel", json={"time_benchmark": [_ROW]})

    assert response.status_code == 200
    assert response.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "benchmark-results.xlsx" in response.headers["Content-Disposition"]
    workbook = openpyxl.load_workbook(io.BytesIO(response.data), read_only=True)
    worksheet = workbook["Benchmark"]
    assert list(worksheet.values)[0] == (
        "Algoritma", "Ukuran Data", "Rata-rata Enkripsi (ms)",
        "Rata-rata Dekripsi (ms)", "Min Enkripsi", "Min Dekripsi",
        "Max Enkripsi", "Max Dekripsi",
    )
    assert list(worksheet.values)[1][0:2] == ("AES-256-GCM", "1 KB")
    workbook.close()


def test_benchmark_export_rejects_missing_data(client):
    response = client.post("/api/benchmark/export/csv", json={})

    assert response.status_code == 400
    assert response.get_json()["success"] is False
