"""
Export Benchmark Results to CSV and Excel (.xlsx).
Menggunakan openpyxl untuk styling spreadsheet yang rapi dan profesional.
"""
import sys
import os
import csv
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import benchmark_service
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def export_csv(results, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["=== BENCHMARK WAKTU ==="])
        writer.writerow(["Algoritma", "Ukuran", "Runs", "Avg Enc (ms)", "Avg Dec (ms)", "Min Enc (ms)", "Min Dec (ms)", "Max Enc (ms)", "Max Dec (ms)"])
        for r in results["time_benchmark"]:
            writer.writerow([
                r["algorithm"], r["size_label"], r["runs"],
                r["avg_encryption_ms"], r["avg_decryption_ms"],
                r["min_encryption_ms"], r["min_decryption_ms"],
                r["max_encryption_ms"], r["max_decryption_ms"]
            ])
        writer.writerow([])
        writer.writerow(["=== KDF PBKDF2 (separate timing) ==="])
        kdf = results["kdf_benchmark"]
        writer.writerow(["Algorithm", "Iterations", "Runs", "Mean ms", "Min ms", "Max ms", "Stddev ms"])
        writer.writerow([kdf["algorithm"], kdf["iterations"], kdf["runs"], kdf["mean_ms"], kdf["min_ms"], kdf["max_ms"], kdf["stddev_ms"]])

        writer.writerow([])
        writer.writerow(["=== AVALANCHE EFFECT (controlled one-bit mutations) ==="])
        writer.writerow(["Algoritma", "Mutasi", "Bit Berubah", "Total Bit", "Avalanche (%)"])
        for av in results["avalanche"]:
            for label, measurement in (("Plaintext bit", av["plaintext_bit_flip"]), ("Key bit", av["key_bit_flip"])):
                writer.writerow([av["algorithm"], label, measurement["changed_bits"], measurement["total_bits"], f"{measurement['percentage']}%"])

        writer.writerow([])
        writer.writerow(["=== SHANNON ENTROPY ==="])
        writer.writerow(["Algoritma", "Plaintext Entropy", "Ciphertext Entropy", "Maksimum"])
        for ent in results["entropy_comparison"]:
            writer.writerow([ent["algorithm"], ent["plaintext_entropy"], ent["ciphertext_entropy"], "8.0000"])


def export_xlsx(results, filepath):
    wb = openpyxl.Workbook()
    
    # ── Styling helpers ──────────────────────────────────────────
    header_fill = PatternFill(start_color="1E3860", end_color="1E3860", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Segoe UI", size=14, bold=True, color="0F1D35")
    data_font = Font(name="Segoe UI", size=10)
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Sheet 1: Waktu Benchmark
    ws_time = wb.active
    ws_time.title = "Benchmark Waktu"
    
    ws_time.merge_cells("A1:H1")
    ws_time["A1"] = "HASIL PENGUJIAN WAKTU ENKRIPSI & DEKRIPSI (ms)"
    ws_time["A1"].font = title_font
    ws_time["A1"].alignment = left_align

    time_headers = ["Algoritma", "Ukuran Data", "Avg Enc (ms)", "Avg Dec (ms)", "Min Enc (ms)", "Min Dec (ms)", "Max Enc (ms)", "Max Dec (ms)"]
    ws_time.append([])
    ws_time.append(time_headers)

    for col_idx in range(1, len(time_headers) + 1):
        cell = ws_time.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    for r in results["time_benchmark"]:
        row_data = [
            r["algorithm"], r["size_label"],
            r["avg_encryption_ms"], r["avg_decryption_ms"],
            r["min_encryption_ms"], r["min_decryption_ms"],
            r["max_encryption_ms"], r["max_decryption_ms"]
        ]
        ws_time.append(row_data)
        current_row = ws_time.max_row
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_time.cell(row=current_row, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = left_align if col_idx <= 2 else center_align

    # Sheet 2: KDF measurement, separated from timed AEAD operations
    ws_kdf = wb.create_sheet(title="PBKDF2 KDF")
    ws_kdf.append(["Algorithm", "Iterations", "Runs", "Mean ms", "Min ms", "Max ms", "Stddev ms"])
    kdf = results["kdf_benchmark"]
    ws_kdf.append([kdf["algorithm"], kdf["iterations"], kdf["runs"], kdf["mean_ms"], kdf["min_ms"], kdf["max_ms"], kdf["stddev_ms"]])

    # Sheet 3: Avalanche analysis for separate plaintext and key bit flips
    ws_av = wb.create_sheet(title="Avalanche Effect")
    ws_av.merge_cells("A1:E1")
    ws_av["A1"] = "AVALANCHE EFFECT - CONTROLLED ONE-BIT MUTATIONS"
    ws_av["A1"].font = title_font
    
    av_headers = ["Algoritma", "Mutasi", "Bit Berubah", "Total Bit", "Avalanche (%)"]
    ws_av.append([])
    ws_av.append(av_headers)
    for col_idx in range(1, len(av_headers) + 1):
        cell = ws_av.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    for av in results["avalanche"]:
        for label, measurement in (("Plaintext bit", av["plaintext_bit_flip"]), ("Key bit", av["key_bit_flip"])):
            row_data = [av["algorithm"], label, measurement["changed_bits"], measurement["total_bits"], f"{measurement['percentage']}%"]
            ws_av.append(row_data)
            current_row = ws_av.max_row
            for col_idx in range(1, len(row_data) + 1):
                cell = ws_av.cell(row=current_row, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                cell.alignment = center_align

    # Sheet 3: Entropy
    ws_ent = wb.create_sheet(title="Shannon Entropy")
    ws_ent.merge_cells("A1:D1")
    ws_ent["A1"] = "HASIL PENGUJIAN SHANNON ENTROPY (Sample 1 KB)"
    ws_ent["A1"].font = title_font

    ent_headers = ["Algoritma", "Plaintext Entropy", "Ciphertext Entropy", "Nilai Maksimum"]
    ws_ent.append([])
    ws_ent.append(ent_headers)
    for col_idx in range(1, len(ent_headers) + 1):
        cell = ws_ent.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    for ent in results["entropy_comparison"]:
        row_data = [ent["algorithm"], f"{ent['plaintext_entropy']:.4f}", f"{ent['ciphertext_entropy']:.4f}", "8.0000"]
        ws_ent.append(row_data)
        current_row = ws_ent.max_row
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_ent.cell(row=current_row, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = center_align

    # Auto-adjust column width for all sheets
    for ws in [ws_time, ws_av, ws_ent]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    wb.save(filepath)


def main():
    ensure_results_dir()
    print("Menjalankan benchmark untuk ekspor...")
    results = benchmark_service.run_full_benchmark(sizes_kb=[1, 1024, 10240], runs=3)

    csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
    xlsx_path = os.path.join(RESULTS_DIR, "benchmark_results.xlsx")

    export_csv(results, csv_path)
    print(f"[+] Berhasil ekspor CSV: {csv_path}")

    export_xlsx(results, xlsx_path)
    print(f"[+] Berhasil ekspor XLSX: {xlsx_path}")


if __name__ == "__main__":
    main()
