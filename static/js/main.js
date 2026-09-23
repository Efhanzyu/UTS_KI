/**
 * Brankas File Tugas Kuliah — Main Global JavaScript
 * Utilitas bersama, penanganan status alert, format ukuran, dan toggle password.
 */

// SVG Icon Helpers
const SVG_ICONS = {
    eye: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`,
    eyeOff: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>`,
    check: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    alert: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    info: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
};

// Helper: Toggle password visibility with SVG icon swap
function togglePassword(inputId, btnEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (btnEl) btnEl.innerHTML = SVG_ICONS.eyeOff;
    } else {
        input.type = 'password';
        if (btnEl) btnEl.innerHTML = SVG_ICONS.eye;
    }
}

// Helper: Show clean inline alert
function showStatus(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;

    let iconSvg = SVG_ICONS.info;
    if (type === 'success') iconSvg = SVG_ICONS.check;
    else if (type === 'error' || type === 'warning') iconSvg = SVG_ICONS.alert;

    el.className = `alert alert-${type}`;
    el.innerHTML = `
        <span class="alert-icon">${iconSvg}</span>
        <div>${escapeHtml(message)}</div>
    `;
    el.style.display = 'flex';
}

// Helper: Hide inline alert
function hideStatus(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'none';
    el.innerHTML = '';
}

// Helper: Format bytes to human readable format
function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Helper: Copy text to clipboard with clean feedback
async function copyToClipboard(text, btnElement, successMsg = 'Berhasil disalin') {
    if (!text) return;
    try {
        await navigator.clipboard.writeText(text);
        showCopyFeedback(btnElement, successMsg);
    } catch (err) {
        // Fallback execution
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showCopyFeedback(btnElement, successMsg);
        } catch (e) {
            console.error('Clipboard copy failed:', e);
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function showCopyFeedback(btnElement, msg) {
    if (!btnElement) return;
    const originalContent = btnElement.innerHTML;
    btnElement.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>${escapeHtml(msg)}</span>
    `;
    btnElement.classList.add('btn-primary');
    btnElement.classList.remove('btn-secondary');
    setTimeout(() => {
        btnElement.innerHTML = originalContent;
        btnElement.classList.remove('btn-primary');
        btnElement.classList.add('btn-secondary');
    }, 2000);
}

// Security Helper: Escape HTML string
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.getElementById('primary-navigation');
    if (!toggle || !nav) return;

    const setOpen = (open) => {
        nav.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Tutup menu' : 'Buka menu');
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', (event) => {
        if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
            setOpen(false);
            toggle.focus();
        }
    });
    window.matchMedia('(min-width: 641px)').addEventListener('change', () => setOpen(false));
});
