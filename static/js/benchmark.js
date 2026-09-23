/**
 * Brankas File Tugas Kuliah — Benchmark & Analytics JavaScript
 * Visualisasi HTML5 Canvas bertema terang, minimalis, dan profesional.
 */

let latestBenchmarkData = null;

// Run Benchmark
async function runBenchmark() {
    const runBtn = document.getElementById('run-benchmark-btn');

    // Collect selected sizes
    const sizes = [];
    if (document.getElementById('size-1kb')?.checked) sizes.push(1);
    if (document.getElementById('size-1mb')?.checked) sizes.push(1024);
    if (document.getElementById('size-10mb')?.checked) sizes.push(10240);

    if (sizes.length === 0) {
        showStatus('bench-status', 'Silakan pilih minimal satu ukuran data uji.', 'warning');
        return;
    }

    const runs = parseInt(document.getElementById('bench-runs')?.value || '10', 10);

    runBtn.disabled = true;
    const originalBtnHtml = runBtn.innerHTML;
    runBtn.innerHTML = `<span>Sedang menguji kriptografi...</span>`;
    showStatus('bench-status', 'Menjalankan pengujian waktu eksekusi, avalanche effect, dan entropy...', 'info');

    try {
        const resp = await fetch('/api/benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sizes_kb: sizes, runs: runs })
        });
        const res = await resp.json();

        if (res.success && res.data) {
            latestBenchmarkData = res.data;

            // Render all sections
            renderTimeTable(res.data.time_benchmark);
            renderKdfResult(res.data.kdf_benchmark);
            renderTimeCharts(res.data.time_benchmark);
            renderAvalanche(res.data.avalanche);
            renderEntropy(res.data.entropy_comparison);
            renderHistogram(res.data.histogram);

            // Show sections
            document.getElementById('section-time').style.display = 'block';
            document.getElementById('section-kdf').style.display = 'block';
            document.getElementById('section-avalanche').style.display = 'block';
            document.getElementById('section-entropy').style.display = 'block';
            document.getElementById('section-histogram').style.display = 'block';

            showStatus('bench-status', 'Benchmark berhasil diselesaikan.', 'success');
        } else {
            showStatus('bench-status', res.message || 'Benchmark gagal dijalankan.', 'error');
        }
    } catch (err) {
        console.error(err);
        showStatus('bench-status', 'Terjadi kesalahan saat menghubungi server benchmark.', 'error');
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = originalBtnHtml;
    }
}

// ── Render Time Table ───────────────────────────────────────────
function renderTimeTable(timeData) {
    const tbody = document.getElementById('time-table-body');
    if (!tbody || !timeData) return;
    tbody.innerHTML = '';

    timeData.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(item.algorithm)}</strong></td>
            <td><code>${escapeHtml(item.size_label)}</code></td>
            <td><strong>${item.avg_encryption_ms.toFixed(3)}</strong></td>
            <td><strong>${item.avg_decryption_ms.toFixed(3)}</strong></td>
            <td>${item.min_encryption_ms.toFixed(3)}</td>
            <td>${item.min_decryption_ms.toFixed(3)}</td>
            <td>${item.max_encryption_ms.toFixed(3)}</td>
            <td>${item.max_decryption_ms.toFixed(3)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ── Render Minimal HTML5 Canvas Bar Charts ──────────────────────
function renderTimeCharts(timeData) {
    drawBarChart('time-chart-enc', timeData, 'avg_encryption_ms', 'Waktu Enkripsi (ms)');
    drawBarChart('time-chart-dec', timeData, 'avg_decryption_ms', 'Waktu Dekripsi (ms)');
}

function drawBarChart(canvasId, timeData, field, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const sizes = [...new Set(timeData.map(d => d.size_label))];
    const algos = ['AES-256-GCM', 'ChaCha20-Poly1305'];
    const colors = {
        'AES-256-GCM': '#0F172A',       // Deep Navy
        'ChaCha20-Poly1305': '#2563EB'  // Restrained Blue
    };

    let maxVal = 0;
    timeData.forEach(d => {
        if (d[field] > maxVal) maxVal = d[field];
    });
    if (maxVal === 0) maxVal = 1;
    maxVal *= 1.25;

    const padding = { top: 30, right: 20, bottom: 40, left: 55 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Draw Subtle Grid Lines & Y-axis Labels
    ctx.strokeStyle = '#E2E8F0';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748B';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'right';

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
        const yVal = (maxVal / ySteps) * i;
        const yPos = padding.top + chartH - (i / ySteps) * chartH;

        ctx.beginPath();
        ctx.moveTo(padding.left, yPos);
        ctx.lineTo(width - padding.right, yPos);
        ctx.stroke();

        ctx.fillText(yVal.toFixed(2), padding.left - 8, yPos + 4);
    }

    // Draw Bars
    const groupWidth = chartW / sizes.length;
    const barWidth = Math.min(36, (groupWidth - 24) / algos.length);

    sizes.forEach((size, sIdx) => {
        const groupCenterX = padding.left + sIdx * groupWidth + groupWidth / 2;

        algos.forEach((algo, aIdx) => {
            const match = timeData.find(d => d.size_label === size && d.algorithm === algo);
            const val = match ? match[field] : 0;
            const barH = (val / maxVal) * chartH;
            const x = groupCenterX + (aIdx - algos.length / 2) * (barWidth + 4) + 2;
            const y = padding.top + chartH - barH;

            // Bar fill
            ctx.fillStyle = colors[algo] || '#0F172A';
            ctx.beginPath();
            if (ctx.roundRect) {
                ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
            } else {
                ctx.rect(x, y, barWidth, barH);
            }
            ctx.fill();

            // Value label above bar
            ctx.fillStyle = '#0F172A';
            ctx.textAlign = 'center';
            ctx.font = '10px Inter, sans-serif';
            ctx.fillText(val.toFixed(2), x + barWidth / 2, Math.max(padding.top + 10, y - 5));
        });

        // X-axis size label
        ctx.fillStyle = '#0F172A';
        ctx.textAlign = 'center';
        ctx.font = '500 11px Inter, sans-serif';
        ctx.fillText(size, groupCenterX, height - 12);
    });

    // Legend
    let legendX = width - padding.right - 230;
    algos.forEach(algo => {
        ctx.fillStyle = colors[algo];
        ctx.fillRect(legendX, 10, 10, 10);
        ctx.fillStyle = '#334155';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(algo, legendX + 16, 19);
        legendX += 115;
    });
}

// ── Render Avalanche Effect ─────────────────────────────────────
function renderKdfResult(item) {
    const tbody = document.getElementById('kdf-table-body');
    if (!tbody || !item) return;
    tbody.innerHTML = '';
    const row = document.createElement('tr');
    row.innerHTML = '<td><strong>' + escapeHtml(item.algorithm) + '</strong></td>' +
        '<td>' + item.iterations.toLocaleString() + '</td><td>' + item.runs + '</td>' +
        '<td>' + item.mean_ms.toFixed(3) + '</td><td>' + item.min_ms.toFixed(3) +
        '</td><td>' + item.max_ms.toFixed(3) + '</td>';
    tbody.appendChild(row);
}

// Avalanche reports changed bits / total ciphertext bits × 100 for two separate one-bit mutations.
function renderAvalanche(avalancheData) {
    const container = document.getElementById('avalanche-results');
    if (!container || !avalancheData) return;
    container.innerHTML = '';

    avalancheData.forEach(item => {
        const card = document.createElement('div');
        card.className = 'feature-box';
        const p = item.plaintext_bit_flip;
        const k = item.key_bit_flip;
        card.innerHTML = '<div><h3 class="feature-box-title">' + escapeHtml(item.algorithm) + '</h3>' +
            '<table class="property-table"><tbody>' +
            '<tr><td>Plaintext bit flip</td><td><strong>' + p.percentage.toFixed(2) + '%</strong></td></tr>' +
            '<tr><td>Key bit flip</td><td><strong>' + k.percentage.toFixed(2) + '%</strong></td></tr>' +
            '<tr><td>Metode</td><td>' + escapeHtml(item.method) + '</td></tr>' +
            '<tr><td>Plaintext mutation</td><td>' + p.changed_bits + ' / ' + p.total_bits + ' bit berubah</td></tr>' +
            '</tbody></table><p class="feature-box-desc">' + escapeHtml(item.note) + '</p></div>';
        container.appendChild(card);
    });
}

function renderEntropy(entropyData) {
    const container = document.getElementById('entropy-results');
    if (!container || !entropyData) return;
    container.innerHTML = '';

    entropyData.forEach(item => {
        const card = document.createElement('div');
        card.className = 'feature-box';
        const pEnt = item.plaintext_entropy;
        const cEnt = item.ciphertext_entropy;

        card.innerHTML = `
            <div>
                <h3 class="feature-box-title">${escapeHtml(item.algorithm)}</h3>
                <div style="display: flex; gap: 24px; margin: 12px 0;">
                    <div>
                        <div style="font-size: 0.8rem; color: #64748B;">Entropy Plaintext</div>
                        <div style="font-size: 1.3rem; font-weight: 600; color: #64748B;">${pEnt.toFixed(4)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8rem; color: #64748B;">Entropy Ciphertext</div>
                        <div style="font-size: 1.3rem; font-weight: 700; color: #15803D;">${cEnt.toFixed(4)}</div>
                    </div>
                </div>
                <p class="feature-box-desc">
                    Estimasi statistik dari distribusi byte sampel; nilai tinggi saja tidak membuktikan keamanan cipher.
                </p>
            </div>
        `;
        container.appendChild(card);
    });
}

// ── Render Byte Histogram ───────────────────────────────────────
function renderHistogram(histogramData) {
    const container = document.getElementById('histogram-container');
    if (!container || !histogramData) return;
    container.innerHTML = '';

    histogramData.forEach((item, idx) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'chart-box mb-4';
        wrapper.innerHTML = `
            <div class="chart-header">${escapeHtml(item.algorithm)} — Distribusi Frekuensi Nilai Byte (0–255)</div>
            <canvas id="hist-canvas-${idx}" width="800" height="180" class="chart-canvas" role="img" aria-label="Histogram byte plaintext dan ciphertext, sumbu X nilai byte 0 sampai 255, sumbu Y frekuensi"></canvas>
            <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 0.82rem; color: #64748B;">
                <span><span style="display:inline-block; width:10px; height:10px; background:rgba(220, 38, 38, 0.4); margin-right:4px;"></span> Plaintext (pola frekuensi)</span>
                <span><span style="display:inline-block; width:10px; height:10px; background:#0F172A; margin-right:4px;"></span> Ciphertext (distribusi seragam)</span>
            </div>
        `;
        container.appendChild(wrapper);

        setTimeout(() => {
            drawHistogramCanvas(`hist-canvas-${idx}`, item.plaintext_histogram, item.ciphertext_histogram);
        }, 10);
    });
}

function drawHistogramCanvas(canvasId, pHist, cHist) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const padding = { top: 15, right: 15, bottom: 25, left: 45 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const maxVal = Math.max(Math.max(...pHist), Math.max(...cHist), 1) * 1.15;

    // Grid / Axes
    ctx.strokeStyle = '#E2E8F0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Y labels
    ctx.fillStyle = '#94A3B8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 2; i++) {
        const val = Math.round((maxVal / 2) * i);
        const y = padding.top + chartH - (i / 2) * chartH;
        ctx.fillText(val, padding.left - 6, y + 3);
    }

    // X labels
    ctx.textAlign = 'center';
    [0, 64, 128, 192, 255].forEach(xVal => {
        const x = padding.left + (xVal / 255) * chartW;
        ctx.fillText(xVal, x, height - padding.bottom + 14);
    });

    const barW = chartW / 256;

    // Plaintext Bars (Red Tint)
    ctx.fillStyle = 'rgba(220, 38, 38, 0.4)';
    for (let i = 0; i < 256; i++) {
        const h = (pHist[i] / maxVal) * chartH;
        const x = padding.left + i * barW;
        const y = padding.top + chartH - h;
        ctx.fillRect(x, y, barW, h);
    }

    // Ciphertext Line (Navy)
    ctx.strokeStyle = '#0F172A';
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    for (let i = 0; i < 256; i++) {
        const h = (cHist[i] / maxVal) * chartH;
        const x = padding.left + i * barW + barW / 2;
        const y = padding.top + chartH - h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.stroke();
}

// ── Export Results ──────────────────────────────────────────────
function exportCSV() {
    if (!latestBenchmarkData || !latestBenchmarkData.time_benchmark) {
        showStatus('bench-status', 'Jalankan benchmark terlebih dahulu sebelum mengekspor data.', 'warning');
        return;
    }

    let csv = 'Algoritma,Ukuran Data,Pengulangan,Avg Enc (ms),Avg Dec (ms),Min Enc (ms),Min Dec (ms),Max Enc (ms),Max Dec (ms)\n';
    latestBenchmarkData.time_benchmark.forEach(row => {
        csv += `"${row.algorithm}","${row.size_label}",${row.runs},${row.avg_encryption_ms},${row.avg_decryption_ms},${row.min_encryption_ms},${row.min_decryption_ms},${row.max_encryption_ms},${row.max_decryption_ms}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    triggerBlobDownload(blob, 'benchmark_results.csv');
}

function exportXLSX() {
    if (!latestBenchmarkData || !latestBenchmarkData.time_benchmark) {
        showStatus('bench-status', 'Jalankan benchmark terlebih dahulu sebelum mengekspor data.', 'warning');
        return;
    }

    let html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">';
    html += '<head><meta charset="utf-8"></head><body>';
    html += '<h3>Hasil Benchmark Kriptografi &mdash; Brankas File Tugas Kuliah</h3>';
    html += '<table border="1"><thead><tr style="background:#0F172A;color:#ffffff">';
    html += '<th>Algoritma</th><th>Ukuran</th><th>Runs</th><th>Avg Enc (ms)</th><th>Avg Dec (ms)</th><th>Min Enc (ms)</th><th>Min Dec (ms)</th><th>Max Enc (ms)</th><th>Max Dec (ms)</th>';
    html += '</tr></thead><tbody>';

    latestBenchmarkData.time_benchmark.forEach(r => {
        html += `<tr><td>${r.algorithm}</td><td>${r.size_label}</td><td>${r.runs}</td><td>${r.avg_encryption_ms}</td><td>${r.avg_decryption_ms}</td><td>${r.min_encryption_ms}</td><td>${r.min_decryption_ms}</td><td>${r.max_encryption_ms}</td><td>${r.max_decryption_ms}</td></tr>`;
    });
    html += '</tbody></table></body></html>';

    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    triggerBlobDownload(blob, 'benchmark_results.xls');
}
