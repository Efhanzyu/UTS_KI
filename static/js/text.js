/**
 * Brankas File Tugas Kuliah — Text Encryption & Decryption JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // Character and Byte counter for plaintext
    const plainInput = document.getElementById('enc-plaintext');
    const counter = document.getElementById('enc-plaintext-counter');
    if (plainInput && counter) {
        const updateCounter = () => {
            const text = plainInput.value;
            const bytes = new TextEncoder().encode(text).length;
            counter.textContent = `${text.length.toLocaleString('id-ID')} karakter (${formatBytes(bytes)})`;
        };
        plainInput.addEventListener('input', updateCounter);
        updateCounter();
    }

    // Auto-clear validation errors when user types (AC-UI-09)
    document.getElementById('enc-plaintext')?.addEventListener('input', () => hideStatus('enc-status'));
    document.getElementById('enc-password')?.addEventListener('input', () => hideStatus('enc-status'));
    document.getElementById('dec-ciphertext')?.addEventListener('input', () => hideStatus('dec-status'));
    document.getElementById('dec-password')?.addEventListener('input', () => hideStatus('dec-status'));

    // Attach form submit listeners
    const encForm = document.getElementById('encrypt-form');
    if (encForm) encForm.addEventListener('submit', handleEncryptSubmit);

    const decForm = document.getElementById('decrypt-form');
    if (decForm) decForm.addEventListener('submit', handleDecryptSubmit);
});

// Tab Switcher for Text Page
function switchTab(tab) {
    const encBtn = document.getElementById('tab-encrypt-btn');
    const decBtn = document.getElementById('tab-decrypt-btn');
    const encPanel = document.getElementById('tab-encrypt');
    const decPanel = document.getElementById('tab-decrypt');

    if (tab === 'encrypt') {
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

// Handle Encrypt Form Submit
async function handleEncryptSubmit(e) {
    e.preventDefault();
    hideStatus('enc-status');

    const plainInput = document.getElementById('enc-plaintext');
    const plaintext = plainInput.value;
    const algorithm = document.getElementById('enc-algorithm').value;
    const passwordInput = document.getElementById('enc-password');
    const password = passwordInput.value;
    const submitBtn = document.getElementById('enc-submit-btn');

    if (!plaintext) {
        showStatus('enc-status', 'Plaintext tidak boleh kosong.', 'error');
        plainInput.focus();
        return;
    }
    if (!password) {
        showStatus('enc-status', 'Password wajib diisi.', 'error');
        passwordInput.focus();
        return;
    }

    submitBtn.disabled = true;
    const originalBtnHtml = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span>Sedang mengenkripsi...</span>`;

    try {
        const resp = await fetch('/api/encrypt/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plaintext, password, algorithm })
        });
        const res = await resp.json();

        if (res.success && res.data) {
            const data = res.data;
            const cipherArea = document.getElementById('enc-ciphertext');
            const copyRow = document.getElementById('enc-copy-row');
            const infoBox = document.getElementById('enc-info');

            cipherArea.value = data.ciphertext_b64;
            copyRow.style.display = 'flex';

            // Populate metadata
            document.getElementById('info-algorithm').textContent = data.algorithm;
            document.getElementById('info-keysize').textContent = `${data.key_size_bits} bit (${data.key_size_bits / 8} bytes)`;
            document.getElementById('info-kdf').textContent = data.kdf;
            document.getElementById('info-iterations').textContent = `${data.pbkdf2_iterations.toLocaleString('id-ID')} putaran`;
            document.getElementById('info-salt').textContent = `${data.salt_size_bytes} bytes`;
            document.getElementById('info-nonce').textContent = `${data.nonce_size_bytes} bytes`;
            document.getElementById('info-ciphersize').textContent = `${data.ciphertext_size_bytes} bytes`;

            infoBox.style.display = 'block';
            showStatus('enc-status', 'Teks berhasil dienkripsi ke format Base64.', 'success');
        } else {
            showStatus('enc-status', res.message || 'Enkripsi teks gagal.', 'error');
        }
    } catch (err) {
        showStatus('enc-status', 'Terjadi kesalahan koneksi ke server.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
    }
}

// Handle Decrypt Form Submit
async function handleDecryptSubmit(e) {
    e.preventDefault();
    hideStatus('dec-status');

    const cipherInput = document.getElementById('dec-ciphertext');
    const ciphertext_b64 = cipherInput.value.trim();
    const passwordInput = document.getElementById('dec-password');
    const password = passwordInput.value;
    const submitBtn = document.getElementById('dec-submit-btn');

    if (!ciphertext_b64) {
        showStatus('dec-status', 'Ciphertext tidak boleh kosong.', 'error');
        cipherInput.focus();
        return;
    }
    if (!password) {
        showStatus('dec-status', 'Password wajib diisi.', 'error');
        passwordInput.focus();
        return;
    }

    submitBtn.disabled = true;
    const originalBtnHtml = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span>Sedang mendekripsi...</span>`;

    try {
        const resp = await fetch('/api/decrypt/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ciphertext_b64, password })
        });
        const res = await resp.json();

        if (res.success && res.data) {
            const plainArea = document.getElementById('dec-plaintext');
            const copyRow = document.getElementById('dec-copy-row');

            plainArea.value = res.data.plaintext;
            copyRow.style.display = 'flex';

            showStatus('dec-status', 'Teks berhasil didekripsi.', 'success');
        } else {
            showStatus('dec-status', res.message || 'Dekripsi gagal: password salah atau ciphertext rusak.', 'error');
        }
    } catch (err) {
        showStatus('dec-status', 'Terjadi kesalahan koneksi ke server.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
    }
}

// Copy Handlers
function copyCiphertext() {
    const text = document.getElementById('enc-ciphertext').value;
    const btn = document.getElementById('copy-cipher-btn');
    copyToClipboard(text, btn, 'Ciphertext tersalin');
}

function copyPlaintext() {
    const text = document.getElementById('dec-plaintext').value;
    const btn = document.getElementById('copy-plain-btn');
    copyToClipboard(text, btn, 'Plaintext tersalin');
}

// Clear Form Handlers
function clearEncryptForm() {
    document.getElementById('encrypt-form').reset();
    document.getElementById('enc-ciphertext').value = '';
    document.getElementById('enc-copy-row').style.display = 'none';
    document.getElementById('enc-info').style.display = 'none';
    hideStatus('enc-status');
    const counter = document.getElementById('enc-plaintext-counter');
    if (counter) counter.textContent = '0 karakter (0 B)';
}

function clearDecryptForm() {
    document.getElementById('decrypt-form').reset();
    document.getElementById('dec-plaintext').value = '';
    document.getElementById('dec-copy-row').style.display = 'none';
    hideStatus('dec-status');
}
