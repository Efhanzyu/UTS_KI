/**
 * Brankas File Tugas Kuliah — File Encryption & Decryption JavaScript
 * Mengelola upload drag & drop, segmented mode switching, dan binary stream download.
 */

let encSelectedFile = null;
let decSelectedFile = null;
let encDownloadBlob = null;
let encDownloadFilename = '';
let decDownloadBlob = null;
let decDownloadFilename = '';

document.addEventListener('DOMContentLoaded', () => {
    setupDropzones();

    const encForm = document.getElementById('file-encrypt-form');
    if (encForm) encForm.addEventListener('submit', handleFileEncrypt);

    const decForm = document.getElementById('file-decrypt-form');
    if (decForm) decForm.addEventListener('submit', handleFileDecrypt);

    // Auto-clear error when user types (AC-UI-09)
    const encPasswordInput = document.getElementById('enc-file-password');
    const decPasswordInput = document.getElementById('dec-file-password');
    if (encPasswordInput) encPasswordInput.addEventListener('input', () => hideStatus('enc-file-status'));
    if (decPasswordInput) decPasswordInput.addEventListener('input', () => hideStatus('dec-file-status'));

    const encDownloadBtn = document.getElementById('enc-download-btn');
    if (encDownloadBtn) {
        encDownloadBtn.addEventListener('click', () => {
            if (encDownloadBlob && encDownloadFilename) {
                triggerBlobDownload(encDownloadBlob, encDownloadFilename);
            }
        });
    }

    const decDownloadBtn = document.getElementById('dec-download-btn');
    if (decDownloadBtn) {
        decDownloadBtn.addEventListener('click', () => {
            if (decDownloadBlob && decDownloadFilename) {
                triggerBlobDownload(decDownloadBlob, decDownloadFilename);
            }
        });
    }

    // Check URL query param or hash for initial mode
    const params = new URLSearchParams(window.location.search);
    if (params.get('mode') === 'decrypt') {
        switchFileMode('decrypt');
    }

    const refreshStoredFilesButton = document.getElementById('refresh-stored-files');
    if (refreshStoredFilesButton) refreshStoredFilesButton.addEventListener('click', loadStoredFiles);
    loadStoredFiles();
});

// Segmented Mode Switcher (Enkripsi vs Dekripsi)
function switchFileMode(mode) {
    const encBtn = document.getElementById('tab-btn-encrypt');
    const decBtn = document.getElementById('tab-btn-decrypt');
    const encPanel = document.getElementById('panel-encrypt');
    const decPanel = document.getElementById('panel-decrypt');

    if (!encBtn || !decBtn || !encPanel || !decPanel) return;

    if (mode === 'encrypt') {
        encBtn.classList.add('active');
        encBtn.setAttribute('aria-selected', 'true');
        decBtn.classList.remove('active');
        decBtn.setAttribute('aria-selected', 'false');

        encPanel.classList.add('active');
        decPanel.classList.remove('active');
    } else {
        decBtn.classList.add('active');
        decBtn.setAttribute('aria-selected', 'true');
        encBtn.classList.remove('active');
        encBtn.setAttribute('aria-selected', 'false');

        decPanel.classList.add('active');
        encPanel.classList.remove('active');
    }
}

// Drag & Drop Setup
function setupDropzones() {
    setupSingleDropzone('enc-dropzone', 'enc-file-input', selectEncFile);
    setupSingleDropzone('dec-dropzone', 'dec-file-input', selectDecFile);
}

function setupSingleDropzone(dropzoneId, inputId, onSelectCallback) {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    if (!dropzone || !input) return;

    // Keyboard support for accessibility (Enter / Space to open file dialog)
    dropzone.setAttribute('tabindex', '0');
    dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            input.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('drag-over');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            onSelectCallback(files[0]);
        }
    });

    input.addEventListener('change', () => {
        if (input.files && input.files.length > 0) {
            onSelectCallback(input.files[0]);
        }
    });
}

function selectEncFile(file) {
    encSelectedFile = file;
    document.getElementById('enc-dropzone').style.display = 'none';
    const infoBox = document.getElementById('enc-file-info');
    document.getElementById('enc-file-name').textContent = file.name;
    document.getElementById('enc-file-size').textContent = formatBytes(file.size);
    infoBox.style.display = 'flex';
    hideStatus('enc-file-status');
}

function clearEncFile() {
    encSelectedFile = null;
    document.getElementById('enc-file-input').value = '';
    document.getElementById('enc-file-info').style.display = 'none';
    document.getElementById('enc-dropzone').style.display = 'block';
    document.getElementById('enc-file-result').style.display = 'none';
    hideStatus('enc-file-status');
}

function selectDecFile(file) {
    decSelectedFile = file;
    document.getElementById('dec-dropzone').style.display = 'none';
    const infoBox = document.getElementById('dec-file-info');
    document.getElementById('dec-file-name').textContent = file.name;
    document.getElementById('dec-file-size').textContent = formatBytes(file.size);
    infoBox.style.display = 'flex';
    hideStatus('dec-file-status');
}

function clearDecFile() {
    decSelectedFile = null;
    document.getElementById('dec-file-input').value = '';
    document.getElementById('dec-file-info').style.display = 'none';
    document.getElementById('dec-dropzone').style.display = 'block';
    document.getElementById('dec-file-result').style.display = 'none';
    hideStatus('dec-file-status');
}

// Handle File Encrypt Submit
async function handleFileEncrypt(e) {
    e.preventDefault();
    hideStatus('enc-file-status');
    document.getElementById('enc-file-result').style.display = 'none';

    if (!encSelectedFile) {
        showStatus('enc-file-status', 'Silakan pilih file yang akan dienkripsi.', 'error');
        return;
    }

    const passwordInput = document.getElementById('enc-file-password');
    const password = passwordInput.value;
    const algorithm = document.getElementById('enc-file-algorithm').value;
    const submitBtn = document.getElementById('enc-file-submit');

    if (!password) {
        showStatus('enc-file-status', 'Password wajib diisi.', 'error');
        passwordInput.focus();
        return;
    }

    const formData = new FormData();
    formData.append('file', encSelectedFile);
    formData.append('password', password);
    formData.append('algorithm', algorithm);

    submitBtn.disabled = true;
    const originalHtml = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span>Sedang mengenkripsi file...</span>`;

    try {
        const resp = await fetch('/api/encrypt/file', {
            method: 'POST',
            body: formData
        });

        const contentType = resp.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            const res = await resp.json();
            showStatus('enc-file-status', res.message || 'Enkripsi file gagal.', 'error');
        } else if (resp.ok) {
            const blob = await resp.blob();
            encDownloadBlob = blob;

            // Extract output filename
            let filename = encSelectedFile.name + '.enc';
            const disposition = resp.headers.get('content-disposition');
            if (disposition && disposition.includes('filename=')) {
                const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match && match[1]) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }
            encDownloadFilename = filename;

            document.getElementById('enc-res-algorithm').textContent = algorithm;
            document.getElementById('enc-res-filename').textContent = filename;
            document.getElementById('enc-res-filesize').textContent = formatBytes(blob.size);
            document.getElementById('enc-file-result').style.display = 'block';

            showStatus('enc-file-status', 'File berhasil dienkripsi! Unduhan berkas .enc dimulai.', 'success');
            loadStoredFiles();

            // Trigger download
            triggerBlobDownload(blob, filename);
        } else {
            showStatus('enc-file-status', 'Gagal memproses file. Kode status: ' + resp.status, 'error');
        }
    } catch (err) {
        showStatus('enc-file-status', 'Terjadi kesalahan jaringan saat mengunggah berkas.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHtml;
    }
}

// Handle File Decrypt Submit
async function handleFileDecrypt(e) {
    e.preventDefault();
    hideStatus('dec-file-status');
    document.getElementById('dec-file-result').style.display = 'none';

    if (!decSelectedFile) {
        showStatus('dec-file-status', 'Silakan pilih file .enc yang akan didekripsi.', 'error');
        return;
    }

    const passwordInput = document.getElementById('dec-file-password');
    const password = passwordInput.value;
    const submitBtn = document.getElementById('dec-file-submit');

    if (!password) {
        showStatus('dec-file-status', 'Password wajib diisi.', 'error');
        passwordInput.focus();
        return;
    }

    const formData = new FormData();
    formData.append('file', decSelectedFile);
    formData.append('password', password);

    submitBtn.disabled = true;
    const originalHtml = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span>Sedang mendekripsi file...</span>`;

    try {
        const resp = await fetch('/api/decrypt/file', {
            method: 'POST',
            body: formData
        });

        const contentType = resp.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            const res = await resp.json();
            showStatus('dec-file-status', res.message || 'Dekripsi gagal: password salah atau data telah dimodifikasi.', 'error');
        } else if (resp.ok) {
            const blob = await resp.blob();
            decDownloadBlob = blob;

            // Extract output filename
            let filename = 'decrypted_file';
            const disposition = resp.headers.get('content-disposition');
            if (disposition && disposition.includes('filename=')) {
                const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match && match[1]) {
                    filename = match[1].replace(/['"]/g, '');
                }
            } else if (decSelectedFile.name.endsWith('.enc')) {
                filename = decSelectedFile.name.slice(0, -4);
            }
            decDownloadFilename = filename;

            document.getElementById('dec-res-filename').textContent = filename;
            document.getElementById('dec-file-result').style.display = 'block';
            showStatus('dec-file-status', 'Dekripsi berhasil! Berkas asli telah dipulihkan.', 'success');

            // Trigger download
            triggerBlobDownload(blob, filename);
        } else {
            showStatus('dec-file-status', 'Dekripsi gagal: password salah atau data telah dimodifikasi.', 'error');
        }
    } catch (err) {
        showStatus('dec-file-status', 'Terjadi kesalahan jaringan saat mengunggah berkas.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHtml;
    }
}

// Download Helper
function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 10000);
}

async function loadStoredFiles() {
    const section = document.getElementById('stored-files-section');
    const list = document.getElementById('stored-files-list');
    if (!section || !list) return;

    try {
        const response = await fetch('/api/storage/files');
        const result = await response.json();
        if (!response.ok || !result.success || !result.data || !result.data.configured) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        const files = result.data.files || [];
        list.innerHTML = files.length ? files.map(renderStoredFile).join('') :
            '<p class="stored-files-empty">Belum ada file terenkripsi tersimpan.</p>';
    } catch (error) {
        section.style.display = 'none';
    }
}

function renderStoredFile(file) {
    return `
        <article class="stored-file-item">
            <div class="stored-file-info">
                <strong>${escapeHtml(file.original_filename)}.enc</strong>
                <span>${escapeHtml(file.algorithm)} / ${formatBytes(file.size_bytes)}</span>
            </div>
            <div class="stored-file-actions">
                <button type="button" class="btn btn-secondary btn-sm" onclick="downloadStoredFile('${file.id}')">Download</button>
                <button type="button" class="btn btn-secondary btn-sm" onclick="decryptStoredFile('${file.id}')">Decrypt</button>
                <button type="button" class="btn btn-ghost btn-sm" onclick="deleteStoredFile('${file.id}')">Delete</button>
            </div>
        </article>
    `;
}

async function downloadStoredFile(fileId) {
    const response = await fetch(`/api/storage/files/${encodeURIComponent(fileId)}`);
    if (!response.ok) {
        showStoredFilesStatus('File tersimpan tidak dapat diunduh.', 'error');
        return;
    }
    triggerBlobDownload(await response.blob(), getDownloadFilename(response, `${fileId}.enc`));
}

async function decryptStoredFile(fileId) {
    const password = window.prompt('Masukkan password file terenkripsi:');
    if (!password) return;
    const response = await fetch(`/api/storage/files/${encodeURIComponent(fileId)}/decrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });
    if (!response.ok) {
        showStoredFilesStatus('Dekripsi file tersimpan gagal.', 'error');
        return;
    }
    triggerBlobDownload(await response.blob(), getDownloadFilename(response, 'decrypted_file'));
}

async function deleteStoredFile(fileId) {
    if (!window.confirm('Hapus file terenkripsi ini dari storage?')) return;
    const response = await fetch(`/api/storage/files/${encodeURIComponent(fileId)}`, { method: 'DELETE' });
    if (!response.ok) {
        showStoredFilesStatus('File tersimpan gagal dihapus.', 'error');
        return;
    }
    loadStoredFiles();
}

function getDownloadFilename(response, fallback) {
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    return match && match[1] ? match[1].replace(/['"]/g, '') : fallback;
}

function showStoredFilesStatus(message, type) {
    showStatus('stored-files-status', message, type);
}