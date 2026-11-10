class ProfilePage {
    constructor() {
        this.form = document.getElementById('profile-form');
        this.fullNameInput = document.getElementById('profile-full-name');
        this.departmentInput = document.getElementById('profile-dept-input');
        this.departmentDisplay = document.getElementById('profile-department');
        this.usernameDisplay = document.getElementById('profile-username');
        this.lastLoginDisplay = document.getElementById('profile-last-login');
        this.widgetCount = document.getElementById('profile-widget-count');
        this.widgetContainer = document.getElementById('profile-widgets');
        this.refreshDisplay = document.getElementById('profile-refresh');
        this.alertBox = document.getElementById('profile-alert');
        this.profileData = window.__USER__ || {};
        this.dashboardConfig = window.__PROFILE_CONFIG__ || {};
        this.init();
    }

    init() {
        this.populateProfile({ user: this.profileData, dashboard_config: this.dashboardConfig });
        this.loadProfileFromApi();
        if (this.form) {
            this.form.addEventListener('submit', (event) => this.handleSubmit(event));
        }
    }

    async loadProfileFromApi() {
        try {
            const response = await fetch('/api/user/profile', {
                credentials: 'include',
            });
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            const data = await response.json();
            this.populateProfile(data);
        } catch (error) {
            console.warn('Unable to refresh profile from API', error);
            this.showAlert('Unable to refresh profile from server. Showing cached values.', 'warning');
        }
    }

    populateProfile(data = {}) {
        if (!data.user) {
            return;
        }
        this.profileData = data.user;
        this.dashboardConfig = data.dashboard_config || this.dashboardConfig || {};

        if (this.fullNameInput) {
            this.fullNameInput.value = this.profileData.full_name || '';
        }
        if (this.departmentInput) {
            this.departmentInput.value = this.profileData.department || '';
        }
        if (this.usernameDisplay) {
            this.usernameDisplay.textContent = this.profileData.username || 'unknown';
        }
        if (this.departmentDisplay) {
            this.departmentDisplay.textContent = this.profileData.department || 'Unassigned';
        }
        if (this.lastLoginDisplay) {
            this.lastLoginDisplay.textContent = this.profileData.last_login || 'tracking pending';
        }
        this.updateWidgets();
    }

    updateWidgets() {
        const widgets = this.dashboardConfig.widgets || [];
        if (this.widgetCount) {
            this.widgetCount.textContent = widgets.length;
        }
        if (this.refreshDisplay) {
            this.refreshDisplay.textContent = this.dashboardConfig.refresh_interval || 30;
        }
        if (!this.widgetContainer) {
            return;
        }
        if (!widgets.length) {
            this.widgetContainer.innerHTML = '<p class="text-sm text-slate-500">All widgets enabled.</p>';
            return;
        }
        this.widgetContainer.innerHTML = widgets
            .map((widget) => `<span class="px-3 py-1 rounded-lg bg-slate-900/70 border border-slate-800 text-xs uppercase tracking-wide">${widget.replace(/-/g, ' ')}</span>`)
            .join('');
    }

    async handleSubmit(event) {
        event.preventDefault();
        const payload = {
            full_name: this.fullNameInput?.value?.trim() || null,
            department: this.departmentInput?.value?.trim() || null,
        };
        try {
            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                throw new Error('Failed to update profile');
            }
            const data = await response.json();
            this.showAlert('Profile updated successfully.', 'success');
            this.populateProfile(data);
        } catch (error) {
            console.error('Profile update failed', error);
            this.showAlert('Unable to update profile right now.', 'error');
        }
    }

    showAlert(message, type = 'success') {
        if (!this.alertBox) {
            return;
        }
        this.alertBox.textContent = message;
        const styles = {
            success: 'border-green-500/50 bg-green-500/10 text-green-200',
            error: 'border-red-500/50 bg-red-500/10 text-red-200',
            warning: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-200',
        };
        this.alertBox.className = `rounded-xl border px-4 py-3 text-sm ${styles[type] || styles.success}`;
        this.alertBox.classList.remove('hidden');
        setTimeout(() => this.alertBox.classList.add('hidden'), 4000);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ProfilePage());
} else {
    new ProfilePage();
}
