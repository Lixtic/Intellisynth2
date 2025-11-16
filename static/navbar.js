class GlobalNavbar {
    constructor() {
        this.mobileMenu = document.getElementById('mobile-menu');
        this.toggleButton = document.getElementById('mobile-menu-toggle');
        this.menuIcon = this.toggleButton ? this.toggleButton.querySelector('i') : null;
        this.realTimeButtons = Array.from(document.querySelectorAll('[data-realtime-toggle]'));
        this.isStandaloneRealtime = true;
        this.init();
    }

    init() {
        this.setupMobileMenu();
        this.setupRealTimeButtons();
    }

    setupMobileMenu() {
        if (!this.mobileMenu || !this.toggleButton) {
            return;
        }

        const closeMenu = () => this.applyMenuState(false);

        this.toggleButton.addEventListener('click', () => {
            const isOpen = this.mobileMenu.classList.contains('mobile-menu-expanded');
            this.applyMenuState(!isOpen);
        });

        this.mobileMenu.querySelectorAll('a, button').forEach((element) => {
            element.addEventListener('click', () => closeMenu());
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth >= 1024) {
                closeMenu();
            }
        });

        closeMenu();
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
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new GlobalNavbar());
} else {
    new GlobalNavbar();
}
