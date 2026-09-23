"""
CLI Benchmark Runner — Brankas File Tugas Kuliah
Menjalankan pengujian kuantitatif performa AES-256-GCM vs ChaCha20-Poly1305.
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import benchmark_service
from config import Config


def print_banner():
    print("=" * 80)
    print("   BRANKAS FILE TUGAS KULIAH — BENCHMARK KRIPTOGRAFI MODERN")
    print("   Pengujian Komparatif: AES-256-GCM vs ChaCha20-Poly1305")
    print("=" * 80)


def format_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    header_str = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(header_str)
    print(sep_str)
    for row in rows:
        print(" | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))


def main():
    print_banner()
    sizes = [1, 1024, 10240]
    runs = Config.BENCHMARK_RUNS
    print(f"\n[1/3] Menjalankan Benchmark Waktu ({len(sizes)} ukuran data, {runs} pengulangan)...")
    
    results = benchmark_service.run_full_benchmark(sizes_kb=sizes, runs=runs)
    
    print("\n[+] HASIL BENCHMARK WAKTU:")
    time_headers = ["Algoritma", "Ukuran", "Avg Enc (ms)", "Avg Dec (ms)", "Min Enc (ms)", "Min Dec (ms)", "Max Enc (ms)", "Max Dec (ms)"]
    time_rows = []
    for r in results["time_benchmark"]:
        time_rows.append([
            r["algorithm"],
            r["size_label"],
            f"{r['avg_encryption_ms']:.3f}",
            f"{r['avg_decryption_ms']:.3f}",
            f"{r['min_encryption_ms']:.3f}",
            f"{r['min_decryption_ms']:.3f}",
            f"{r['max_encryption_ms']:.3f}",
            f"{r['max_decryption_ms']:.3f}",
        ])
    format_table(time_rows, time_headers)

    print("\n[+] HASIL DERIVASI KUNCI PBKDF2 (diukur terpisah):")
    kdf = results["kdf_benchmark"]
    print(f"{kdf['algorithm']} ({kdf['iterations']} iterasi, {kdf['runs']} pengulangan): "
          f"mean {kdf['mean_ms']:.3f} ms, min {kdf['min_ms']:.3f} ms, max {kdf['max_ms']:.3f} ms")

    print("\n[2/3] HASIL AVALANCHE EFFECT (mutasi satu bit plaintext dan key):")
    av_headers = ["Algoritma", "Mutasi", "Bit Berubah", "Total Bit", "Avalanche (%)"]
    av_rows = []
    for av in results["avalanche"]:
        for label, measurement in (("Plaintext bit", av["plaintext_bit_flip"]), ("Key bit", av["key_bit_flip"])):
            av_rows.append([
                av["algorithm"], label, measurement["changed_bits"], measurement["total_bits"],
                f"{measurement['percentage']:.2f}%"
            ])
    format_table(av_rows, av_headers)

    print("\n[3/3] HASIL SHANNON ENTROPY (Sample 1 KB):")
    ent_headers = ["Algoritma", "Plaintext Entropy", "Ciphertext Entropy", "Rasio Keacakan (Max 8.0)"]
    ent_rows = []
    for ent in results["entropy_comparison"]:
        c_ent = ent["ciphertext_entropy"]
        ent_rows.append([
            ent["algorithm"],
            f"{ent['plaintext_entropy']:.4f}",
            f"{c_ent:.4f}",
            f"{(c_ent / 8.0 * 100):.1f}%"
        ])
    format_table(ent_rows, ent_headers)

    print("\n" + "=" * 80)
    print("   PENGUJIAN BENCHMARK SELESAI DENGAN SUKSES")
    print("=" * 80)


if __name__ == "__main__":
    main()
