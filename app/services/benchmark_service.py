"""Measured cryptographic benchmark and analysis helpers."""
import math, os, secrets, statistics, time
from typing import Any
from app.crypto import aes_gcm, chacha20, kdf as kdf_module
from config import Config
ALGORITHM_AES="AES-256-GCM"
ALGORITHM_CHACHA="ChaCha20-Poly1305"
ALGORITHMS=(ALGORITHM_AES,ALGORITHM_CHACHA)

def _get_crypto_module(algorithm):
    if algorithm==ALGORITHM_AES:return aes_gcm
    if algorithm==ALGORITHM_CHACHA:return chacha20
    raise ValueError(f"Algoritma tidak didukung: {algorithm}")

def _derive_benchmark_key(iterations):
    password=secrets.token_urlsafe(32)
    return kdf_module.derive_key(password,kdf_module.generate_salt(),iterations)

def _summary(values):
    return {"mean_ms":round(statistics.mean(values),4),"min_ms":round(min(values),4),
            "max_ms":round(max(values),4),"stddev_ms":round(statistics.pstdev(values),4)}

def _format_size(size_kb):
    return f"{size_kb} KB" if size_kb<1024 else f"{size_kb//1024} MB"

def run_time_benchmark(size_kb,algorithm,runs=None,kdf_iterations=None):
    runs=Config.BENCHMARK_RUNS if runs is None else runs
    kdf_iterations=Config.BENCHMARK_KDF_ITERATIONS if kdf_iterations is None else kdf_iterations
    if not 1<=runs<=Config.BENCHMARK_MAX_RUNS: raise ValueError("runs harus berada antara 1 dan 100.")
    crypto=_get_crypto_module(algorithm); data=os.urandom(size_kb*1024)
    key=_derive_benchmark_key(kdf_iterations); enc=[]; dec=[]
    for _ in range(runs):
        nonce=crypto.generate_nonce()
        started=time.perf_counter(); ciphertext=crypto.encrypt(key,data,nonce); enc.append((time.perf_counter()-started)*1000)
        started=time.perf_counter(); crypto.decrypt(key,ciphertext,nonce); dec.append((time.perf_counter()-started)*1000)
    e=_summary(enc); d=_summary(dec); label=_format_size(size_kb)
    return {"algorithm":algorithm,"data_size":label,"size_kb":size_kb,"size_bytes":size_kb*1024,"size_label":label,"runs":runs,
            "encryption_times_ms":[round(x,4) for x in enc],"decryption_times_ms":[round(x,4) for x in dec],
            "encrypt_mean_ms":e["mean_ms"],"encrypt_min_ms":e["min_ms"],"encrypt_max_ms":e["max_ms"],"encrypt_stddev_ms":e["stddev_ms"],
            "decrypt_mean_ms":d["mean_ms"],"decrypt_min_ms":d["min_ms"],"decrypt_max_ms":d["max_ms"],"decrypt_stddev_ms":d["stddev_ms"],
            "avg_encryption_ms":e["mean_ms"],"avg_decryption_ms":d["mean_ms"],"min_encryption_ms":e["min_ms"],"min_decryption_ms":d["min_ms"],"max_encryption_ms":e["max_ms"],"max_decryption_ms":d["max_ms"]}

def run_kdf_benchmark(runs=None,iterations=None):
    runs=Config.BENCHMARK_RUNS if runs is None else runs
    iterations=Config.PBKDF2_ITERATIONS if iterations is None else iterations
    if not 1<=runs<=Config.BENCHMARK_MAX_RUNS: raise ValueError("runs harus berada antara 1 dan 100.")
    times=[]
    for _ in range(runs):
        password=secrets.token_urlsafe(32); salt=kdf_module.generate_salt()
        start=time.perf_counter(); kdf_module.derive_key(password,salt,iterations); times.append((time.perf_counter()-start)*1000)
    return {"algorithm":"PBKDF2-HMAC-SHA256","iterations":iterations,"runs":runs,"times_ms":[round(x,4) for x in times],**_summary(times)}

def _compare_bits(a,b):
    total=max(len(a),len(b))*8; shared=min(len(a),len(b))
    changed=sum((x^y).bit_count() for x,y in zip(a[:shared],b[:shared]))+abs(len(a)-len(b))*8
    return {"changed_bits":changed,"total_bits":total,"percentage":round(changed*100/total,2) if total else 0.0}

def calculate_avalanche_test_only(algorithm,plaintext_size=64,kdf_iterations=None):
    """TEST ONLY. NEVER REUSE NONCE IN PRODUCTION ENCRYPTION."""
    if plaintext_size<1: raise ValueError("Ukuran eksperimen harus minimal satu byte.")
    kdf_iterations=Config.BENCHMARK_KDF_ITERATIONS if kdf_iterations is None else kdf_iterations
    crypto=_get_crypto_module(algorithm); key_a=_derive_benchmark_key(kdf_iterations); key_b=bytearray(key_a); key_b[0]^=1
    nonce=crypto.generate_nonce(); plain_a=os.urandom(plaintext_size); plain_b=bytes([plain_a[0]^1])+plain_a[1:]
    # TEST ONLY: controlled nonce reuse isolates mutations; never call from production encryption paths.
    p=_compare_bits(crypto.encrypt(key_a,plain_a,nonce),crypto.encrypt(key_a,plain_b,nonce))
    k=_compare_bits(crypto.encrypt(key_a,plain_a,nonce),crypto.encrypt(bytes(key_b),plain_a,nonce))
    return {"algorithm":algorithm,"plaintext_size_bytes":plaintext_size,"method":"Single-bit mutation",
            "plaintext_bit_flip":p,"key_bit_flip":k,"changed_ciphertext_bits":p["changed_bits"],
            "total_ciphertext_bits":p["total_bits"],"avalanche_percentage":p["percentage"],
            "note":"Eksperimen parameter terkendali; tidak mewakili konfigurasi enkripsi produksi."}

def calculate_entropy(data):
    if not data:return 0.0
    freq=[0]*256
    for b in data:freq[b]+=1
    total=len(data)
    return round(-sum((n/total)*math.log2(n/total) for n in freq if n),6)

def calculate_histogram(data):
    freq=[0]*256
    for b in data:freq[b]+=1
    return freq

def run_full_benchmark(sizes_kb=None,runs=None):
    sizes_kb=[1,1024,10240] if sizes_kb is None else sizes_kb
    runs=Config.BENCHMARK_RUNS if runs is None else runs
    if not 1<=runs<=Config.BENCHMARK_MAX_RUNS:raise ValueError("runs harus berada antara 1 dan 100.")
    result={"time_benchmark":[],"kdf_benchmark":run_kdf_benchmark(runs),"avalanche":[],"entropy_comparison":[],"histogram":[],
            "methodology":{"cipher_timing":"PBKDF2 key derived before timed AEAD operations.","kdf_timing":"PBKDF2 measured separately at production iteration count.","runs":runs}}
    for size in sizes_kb:
        for algo in ALGORITHMS:result["time_benchmark"].append(run_time_benchmark(size,algo,runs))
    for algo in ALGORITHMS:result["avalanche"].append(calculate_avalanche_test_only(algo))
    sample=os.urandom(1024)
    for algo in ALGORITHMS:
        crypto=_get_crypto_module(algo); key=_derive_benchmark_key(Config.BENCHMARK_KDF_ITERATIONS)
        cipher=crypto.encrypt(key,sample,crypto.generate_nonce())
        result["entropy_comparison"].append({"algorithm":algo,"plaintext_entropy":calculate_entropy(sample),"ciphertext_entropy":calculate_entropy(cipher)})
        result["histogram"].append({"algorithm":algo,"plaintext_histogram":calculate_histogram(sample),"ciphertext_histogram":calculate_histogram(cipher)})
    return result
