class GlobalNavbar {
    constructor() {
        this.mobileMenu = document.getElementById('mobile-menu');
        this.toggleButton = document.getElementById('mobile-menu-toggle');
        this.menuIcon = this.toggleButton ? this.toggleButton.querySelector('i') : null;
        this.realTimeButtons = Array.from(document.querySelectorAll('[data-realtime-toggle]'));
        this.isStandaloneRealtime = true;
        this.userMenuTrigger = document.getElementById('user-menu-trigger');
        this.userMenu = document.getElementById('user-menu');
        this.logoutButtons = Array.from(document.querySelectorAll('[data-logout]'));
        this.redirecting = false;
        this.init();
    }

    init() {
        this.setupMobileMenu();
        this.setupRealTimeButtons();
        this.setupUserMenu();
        this.setupLogoutButtons();
    }

    setupMobileMenu() {
        if (!this.mobileMenu || !this.toggleButton) {
            return;
        }

        // Ensure initial state is properly set
        this.mobileMenu.classList.add('mobile-menu-collapsed');
        this.mobileMenu.classList.remove('mobile-menu-expanded');

        this.toggleButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const isOpen = this.mobileMenu.classList.contains('mobile-menu-expanded');
            this.applyMenuState(!isOpen);
        });

        this.mobileMenu.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                // Small delay to allow navigation to complete
                setTimeout(() => this.applyMenuState(false), 100);
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            const isOpen = this.mobileMenu.classList.contains('mobile-menu-expanded');
            if (!isOpen) return;

            // Check if click is outside both menu and toggle button
            const isClickInsideMenu = this.mobileMenu.contains(e.target);
            const isClickOnToggle = this.toggleButton.contains(e.target);

            if (!isClickInsideMenu && !isClickOnToggle) {
                this.applyMenuState(false);
            }
        });

        // Close menu when touching/tapping outside (mobile-specific)
        document.addEventListener('touchstart', (e) => {
            const isOpen = this.mobileMenu.classList.contains('mobile-menu-expanded');
            if (!isOpen) return;

            const isClickInsideMenu = this.mobileMenu.contains(e.target);
            const isClickOnToggle = this.toggleButton.contains(e.target);

            if (!isClickInsideMenu && !isClickOnToggle) {
                this.applyMenuState(false);
            }
        }, { passive: true });

        window.addEventListener('resize', () => {
            if (window.innerWidth >= 1024) {
                this.applyMenuState(false);
            }
        });
    }

    applyMenuState(isOpen) {
        if (!this.mobileMenu || !this.toggleButton) {
            return;
        }
        this.mobileMenu.classList.toggle('mobile-menu-expanded', isOpen);
        this.mobileMenu.classList.toggle('mobile-menu-collapsed', !isOpen);
        this.toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        this.toggleButton.dataset.menuOpen = isOpen ? 'true' : 'false';
        if (this.menuIcon) {
            this.menuIcon.classList.toggle('fa-bars', !isOpen);
            this.menuIcon.classList.toggle('fa-times', isOpen);
        }
    }

    setupRealTimeButtons() {
        if (!this.realTimeButtons.length) {
            return;
        }

        this.realTimeButtons.forEach((button) => {
            button.addEventListener('click', () => this.handleRealTimeToggle());
        });
    }

    handleRealTimeToggle() {
        if (window.dashboard && typeof window.dashboard.toggleRealTime === 'function') {
            window.dashboard.toggleRealTime();
            return;
        }

        if (typeof window.toggleRealTime === 'function') {
            window.toggleRealTime();
            return;
        }

        this.isStandaloneRealtime = !this.isStandaloneRealtime;
        this.renderStandaloneRealtime();
    }

    renderStandaloneRealtime() {
        this.realTimeButtons.forEach((button) => {
            const activeClass = button.dataset.activeClass || button.className;
            const inactiveClass = button.dataset.inactiveClass || button.className;
            button.className = this.isStandaloneRealtime ? activeClass : inactiveClass;

            if (button.classList.contains('flex')) {
                button.innerHTML = this.isStandaloneRealtime
                    ? '<i class="fas fa-sync-alt mr-1"></i><span class="hidden sm:inline">Real-time</span><span class="sm:hidden">RT</span>'
                    : '<i class="fas fa-pause mr-1"></i><span class="hidden sm:inline">Paused</span><span class="sm:hidden">||</span>';
            } else {
                button.innerHTML = this.isStandaloneRealtime
                    ? '<i class="fas fa-sync-alt mr-1"></i>Real-time'
                    : '<i class="fas fa-pause mr-1"></i>Paused';
            }
        });
    }

    setupUserMenu() {
        if (!this.userMenuTrigger || !this.userMenu) {
            return;
        }

        this.userMenuTrigger.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const isVisible = !this.userMenu.classList.contains('hidden');
            this.toggleUserMenu(!isVisible);
        });

        document.addEventListener('click', (event) => {
            if (!this.userMenu || this.userMenu.classList.contains('hidden')) {
                return;
            }
            if (
                this.userMenuTrigger.contains(event.target) ||
                this.userMenu.contains(event.target)
            ) {
                return;
            }
            this.toggleUserMenu(false);
        });
    }

    toggleUserMenu(show) {
        if (!this.userMenu) {
            return;
        }
        if (show) {
            this.userMenu.classList.remove('hidden');
            this.userMenuTrigger?.setAttribute('aria-expanded', 'true');
        } else {
            this.userMenu.classList.add('hidden');
            this.userMenuTrigger?.setAttribute('aria-expanded', 'false');
        }
    }

    setupLogoutButtons() {
        if (!this.logoutButtons.length) {
            return;
        }
        this.logoutButtons.forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                this.handleLogout();
            });
        });
    }

    async handleLogout() {
        if (this.redirecting) {
            return;
        }
        this.redirecting = true;
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (error) {
            console.warn('Logout failed', error);
        } finally {
            window.location.href = '/login';
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new GlobalNavbar());
} else {
    new GlobalNavbar();
}
