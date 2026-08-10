/* ============================================================
   CareBridge AI — Auth JavaScript
   Handles: Login, Signup, Password toggle, Strength, Particles
   ============================================================ */

'use strict';

// ── Helpers ──────────────────────────────────────────────────

/**
 * Show an alert notification in the #auth-alert element.
 * @param {string} message
 * @param {'success'|'error'} type
 */
function showAlert(message, type) {
    const box = document.getElementById('auth-alert');
    if (!box) return;

    const icon = type === 'success'
        ? '<i class="fa-solid fa-circle-check"></i>'
        : '<i class="fa-solid fa-circle-exclamation"></i>';

    box.innerHTML = icon + ' ' + message;
    box.className = 'alert ' + type;

    // Scroll alert into view
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Auto-hide after 6 seconds
    clearTimeout(box._hideTimer);
    box._hideTimer = setTimeout(() => {
        box.classList.add('hidden');
    }, 6000);
}

/**
 * Set a button to loading state.
 * @param {HTMLButtonElement} btn
 * @param {string} originalText
 */
function setLoading(btn, originalText) {
    btn.innerHTML = '<div class="spinner"></div>';
    btn.disabled = true;
    btn.dataset.originalText = originalText;
}

/**
 * Reset a button from loading state.
 * @param {HTMLButtonElement} btn
 * @param {string} text
 */
function resetBtn(btn, text) {
    btn.innerHTML = '<span>' + text + '</span>';
    btn.disabled = false;
}

// ── Password Toggle ───────────────────────────────────────────

function initPasswordToggle(toggleId, iconId, inputId) {
    const toggle = document.getElementById(toggleId);
    const icon   = document.getElementById(iconId);
    const input  = document.getElementById(inputId);

    if (!toggle || !icon || !input) return;

    toggle.addEventListener('click', () => {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        icon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
    });
}

// ── Password Strength ─────────────────────────────────────────

function initPasswordStrength() {
    const pwdInput  = document.getElementById('password');
    const container = document.getElementById('pwdStrength');
    const label     = document.getElementById('pwdStrengthLabel');
    const segs      = [
        document.getElementById('seg1'),
        document.getElementById('seg2'),
        document.getElementById('seg3'),
        document.getElementById('seg4'),
    ];

    if (!pwdInput || !container) return;

    pwdInput.addEventListener('input', () => {
        const val = pwdInput.value;

        if (!val) {
            container.style.display = 'none';
            segs.forEach(s => s && (s.className = 'pwd-bar-seg'));
            return;
        }

        container.style.display = 'block';

        // Score 0–4
        let score = 0;
        if (val.length >= 8)  score++;
        if (/[A-Z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;

        const levels = ['', 'weak', 'fair', 'good', 'strong'];
        const labels = ['', 'Weak — add uppercase & numbers', 'Fair — add a symbol', 'Good — almost there!', 'Strong password ✓'];

        segs.forEach((s, i) => {
            if (!s) return;
            s.className = 'pwd-bar-seg' + (i < score ? ' ' + levels[score] : '');
        });

        if (label) {
            label.textContent = labels[score] || '';
            label.style.color = score === 4 ? '#10b981'
                               : score === 3 ? '#eab308'
                               : score === 2 ? '#f97316'
                               : '#ef4444';
        }
    });
}

// ── Floating Particles ────────────────────────────────────────

function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    const count = 20;
    for (let i = 0; i < count; i++) {
        const p = document.createElement('div');
        p.className = 'particle';

        const size = Math.random() * 4 + 2;
        p.style.cssText = `
            width:  ${size}px;
            height: ${size}px;
            left:   ${Math.random() * 100}%;
            animation-duration:  ${Math.random() * 15 + 10}s;
            animation-delay:     ${Math.random() * 8}s;
            opacity: ${Math.random() * 0.5 + 0.1};
            background: ${Math.random() > 0.5
                ? 'rgba(99,102,241,0.5)'
                : 'rgba(6,182,212,0.5)'};
        `;
        container.appendChild(p);
    }
}

// ── Login Form ────────────────────────────────────────────────

function initLoginForm() {
    const form = document.getElementById('loginForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email    = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const btn      = document.getElementById('loginBtn');
        const btnText  = document.getElementById('loginBtnText');

        // Client-side validation
        if (!email) {
            showAlert('Please enter your email address.', 'error');
            document.getElementById('email').focus();
            return;
        }
        if (!password) {
            showAlert('Please enter your password.', 'error');
            document.getElementById('password').focus();
            return;
        }

        // Loading state
        setLoading(btn, 'Sign In');

        try {
            const response = await fetch('/api/auth/login', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                // Persist token & user data
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));

                showAlert('Login successful! Redirecting to your dashboard…', 'success');

                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1400);
            } else {
                const msg = data.message || 'Login failed. Please check your credentials.';
                showAlert(msg, 'error');
                resetBtn(btn, 'Sign In');
            }
        } catch (err) {
            console.error('Login error:', err);
            showAlert('Network error. Please check your connection and try again.', 'error');
            resetBtn(btn, 'Sign In');
        }
    });
}

// ── Signup Form ───────────────────────────────────────────────

function initSignupForm() {
    const form = document.getElementById('signupForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn     = document.getElementById('signupBtn');
        const btnText = document.getElementById('signupBtnText');

        // Collect fields
        const fullName    = document.getElementById('fullName')?.value.trim();
        const email       = document.getElementById('email')?.value.trim();
        const mobile      = document.getElementById('mobileNumber')?.value.trim();
        const age         = document.getElementById('age')?.value.trim();
        const gender      = document.getElementById('gender')?.value;
        const country     = document.getElementById('country')?.value.trim();
        const language    = document.getElementById('language')?.value;
        const emergency   = document.getElementById('emergencyContact')?.value.trim();
        const password    = document.getElementById('password')?.value;
        const confirmPwd  = document.getElementById('confirmPassword')?.value;
        const termsChecked = document.getElementById('terms')?.checked;

        // Client-side validation
        if (!fullName) {
            showAlert('Please enter your full name.', 'error');
            document.getElementById('fullName').focus();
            return;
        }
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showAlert('Please enter a valid email address.', 'error');
            document.getElementById('email').focus();
            return;
        }
        if (!mobile) {
            showAlert('Please enter your mobile number.', 'error');
            document.getElementById('mobileNumber').focus();
            return;
        }
        if (!password || password.length < 8) {
            showAlert('Password must be at least 8 characters long.', 'error');
            document.getElementById('password').focus();
            return;
        }
        if (password !== confirmPwd) {
            showAlert('Passwords do not match. Please re-enter.', 'error');
            document.getElementById('confirmPassword').focus();
            return;
        }
        if (!termsChecked) {
            showAlert('You must agree to the Terms of Service and Privacy Policy.', 'error');
            return;
        }

        // Build payload (exclude UI-only fields)
        const payload = {
            full_name:          fullName,
            email:              email,
            mobile_number:      mobile,
            password:           password,
        };
        if (age)       payload.age       = parseInt(age, 10);
        if (gender)    payload.gender    = gender;
        if (country)   payload.country   = country;
        if (language)  payload.preferred_language = language;
        if (emergency) payload.emergency_contact   = emergency;

        // Loading state
        setLoading(btn, 'Create Free Account');

        try {
            const response = await fetch('/api/auth/signup', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok) {
                showAlert('Account created successfully! Redirecting to login…', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                const msg = result.message || 'Signup failed. Please try again.';
                showAlert(msg, 'error');
                resetBtn(btn, 'Create Free Account');
            }
        } catch (err) {
            console.error('Signup error:', err);
            showAlert('Network error. Please check your connection and try again.', 'error');
            resetBtn(btn, 'Create Free Account');
        }
    });
}

// ── Auth Guard (Dashboard) ────────────────────────────────────

/**
 * Call this on protected pages. Redirects to login if no token found.
 */
function requireAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return null;
    }
    return token;
}

/**
 * Get the Authorization header for API calls.
 */
function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': 'Bearer ' + token } : {};
}

// ── Logout ────────────────────────────────────────────────────

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Expose globally for use in other scripts
window.CareBridgeAuth = { requireAuth, getAuthHeader, logout, showAlert };

// ── Init ──────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Particles on all auth pages
    initParticles();

    // Login page
    initLoginForm();
    initPasswordToggle('togglePwd', 'togglePwdIcon', 'password');

    // Signup page
    initSignupForm();
    initPasswordStrength();
    initPasswordToggle('togglePwd', 'togglePwdIcon', 'password');
    initPasswordToggle('toggleConfirmPwd', 'toggleConfirmPwdIcon', 'confirmPassword');

    // Google Login Trigger
    const googleBtn = document.getElementById('googleBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            window.location.href = '/api/auth/google';
        });
    }

    // If already logged in, skip auth pages
    const isAuthPage = document.getElementById('loginForm') || document.getElementById('signupForm');
    if (isAuthPage && localStorage.getItem('access_token')) {
        window.location.href = '/dashboard';
    }
});
