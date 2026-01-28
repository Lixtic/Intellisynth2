document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const alertBox = document.getElementById('auth-alert');

    function showAlert(message, type = 'error') {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.classList.remove('hidden');
        alertBox.classList.toggle('border-green-500/40', type === 'success');
        alertBox.classList.toggle('bg-green-500/10', type === 'success');
        alertBox.classList.toggle('text-green-200', type === 'success');
        alertBox.classList.toggle('border-red-500/40', type !== 'success');
        alertBox.classList.toggle('bg-red-500/10', type !== 'success');
        alertBox.classList.toggle('text-red-200', type !== 'success');
    }

    function clearAlert() {
        if (!alertBox) return;
        alertBox.classList.add('hidden');
        alertBox.textContent = '';
    }

    function toggleMode(showLogin) {
        if (!loginForm || !registerForm) return;
        clearAlert();
        loginForm.classList.toggle('hidden', !showLogin);
        registerForm.classList.toggle('hidden', showLogin);
        loginTab?.classList.toggle('bg-white', showLogin);
        loginTab?.classList.toggle('text-slate-900', showLogin);
        loginTab?.classList.toggle('border', !showLogin);
        loginTab?.classList.toggle('border-white/20', !showLogin);
        registerTab?.classList.toggle('bg-white', !showLogin);
        registerTab?.classList.toggle('text-slate-900', !showLogin);
        registerTab?.classList.toggle('border', showLogin);
        registerTab?.classList.toggle('border-white/20', showLogin);
    }

    async function submitAuth(endpoint, payload) {
        clearAlert();
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            showAlert('Success! Redirecting…', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 400);
        } catch (error) {
            showAlert(error.message || 'Something went wrong');
        }
    }

    loginForm?.addEventListener('submit', (event) => {
        event.preventDefault();
        const payload = {
            username: (document.getElementById('login-username')?.value || '').trim(),
            password: document.getElementById('login-password')?.value || '',
        };
        submitAuth('/api/auth/login', payload);
    });

    registerForm?.addEventListener('submit', (event) => {
        event.preventDefault();
        const payload = {
            username: (document.getElementById('register-username')?.value || '').trim(),
            email: (document.getElementById('register-email')?.value || '').trim(),
            password: document.getElementById('register-password')?.value || '',
            full_name: (document.getElementById('register-full-name')?.value || '').trim() || undefined,
            department: (document.getElementById('register-department')?.value || '').trim() || undefined,
        };
        submitAuth('/api/auth/register', payload);
    });

    loginTab?.addEventListener('click', () => toggleMode(true));
    registerTab?.addEventListener('click', () => toggleMode(false));
    showRegisterLink?.addEventListener('click', () => toggleMode(false));
    showLoginLink?.addEventListener('click', () => toggleMode(true));
});
