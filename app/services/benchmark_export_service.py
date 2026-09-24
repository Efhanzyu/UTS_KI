"""In-memory exports for the benchmark table."""
from __future__ import annotations

import csv
import io
from typing import Any

import openpyxl
from openpyxl.styles import Font


TIME_HEADERS = (
    "Algoritma",
    "Ukuran Data",
    "Rata-rata Enkripsi (ms)",
    "Rata-rata Dekripsi (ms)",
    "Min Enkripsi",
    "Min Dekripsi",
    "Max Enkripsi",
    "Max Dekripsi",
)

_TIME_FIELDS = (
    "algorithm",
    "size_label",
    "avg_encryption_ms",
    "avg_decryption_ms",
    "min_encryption_ms",
    "min_decryption_ms",
    "max_encryption_ms",
    "max_decryption_ms",
)


def _time_rows(data: Any) -> list[list[Any]]:
    """Validate and normalize the rows currently rendered by the benchmark page."""
    if not isinstance(data, dict) or not isinstance(data.get("time_benchmark"), list):
        raise ValueError("Data benchmark tidak tersedia.")

    rows = []
    for item in data["time_benchmark"]:
        if not isinstance(item, dict) or any(field not in item for field in _TIME_FIELDS):
            raise ValueError("Format data benchmark tidak valid.")
        rows.append([item[field] for field in _TIME_FIELDS])
    if not rows:
        raise ValueError("Data benchmark tidak tersedia.")
    return rows


def csv_bytes(data: Any) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(TIME_HEADERS)
    writer.writerows(_time_rows(data))
    return output.getvalue().encode("utf-8-sig")


def xlsx_bytes(data: Any) -> bytes:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Benchmark"
    worksheet.append(list(TIME_HEADERS))
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
    worksheet.freeze_panes = "A2"
    for row in _time_rows(data):
        worksheet.append(row)
    for column in worksheet.columns:
        letter = column[0].column_letter
        worksheet.column_dimensions[letter].width = min(
            max(len(str(cell.value or "")) for cell in column) + 2, 32
        )

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output.getvalue()
