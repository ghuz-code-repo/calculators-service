/**
 * Theme Manager для калькуляторов Golden House
 */

// КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ FOUC - Немедленное применение темы
(function() {
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
    
    // Получаем тему из cookies или localStorage
    const cookieTheme = getCookie('gh_theme');
    const savedTheme = cookieTheme || localStorage.getItem('gh_theme_preference') || 'light';
    
    // Применяем тему НЕМЕДЛЕННО
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-theme');
        if (document.body) {
            document.body.classList.add('dark-theme');
        } else {
            // Если body еще не готов
            const observer = new MutationObserver(function(mutations, obs) {
                if (document.body) {
                    document.body.classList.add('dark-theme');
                    obs.disconnect();
                }
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });
        }
    }
    
    // Синхронизируем localStorage и cookies
    if (cookieTheme && cookieTheme !== localStorage.getItem('gh_theme_preference')) {
        localStorage.setItem('gh_theme_preference', cookieTheme);
    } else if (!cookieTheme && localStorage.getItem('gh_theme_preference')) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (365 * 24 * 60 * 60 * 1000));
        document.cookie = `gh_theme=${localStorage.getItem('gh_theme_preference')};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }
})();

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'gh_theme_preference';
        this.COOKIE_KEY = 'gh_theme';
        this.DARK_THEME_CLASS = 'dark-theme';
        this.themes = {
            light: 'light',
            dark: 'dark'
        };
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }

        // Слушаем изменения между вкладками
        window.addEventListener('storage', (e) => {
            if (e.key === this.STORAGE_KEY && e.newValue !== e.oldValue) {
                const newTheme = e.newValue || this.themes.light;
                this.applyTheme(newTheme, false);
                this.setCookie(this.COOKIE_KEY, newTheme, 365);
            }
        });
    }

    initializeComponents() {
        this.findThemeSwitcher();
        this.initMobileMenu();
        this.loadLogoUrls();
        
        const currentTheme = this.getCurrentTheme();
        this.updateSwitcherUI(currentTheme);
        this.updateLogo(currentTheme);
    }

    findThemeSwitcher() {
        this.themeSwitcher = document.getElementById('theme-switcher');
        if (!this.themeSwitcher) {
            console.warn('Theme switcher not found in header');
        }
    }

    initMobileMenu() {
        const mobileToggle = document.getElementById('mobileMenuToggle');
        const mobileNav = document.getElementById('mobileNav');
        
        if (mobileToggle && mobileNav) {
            mobileToggle.addEventListener('click', () => {
                mobileToggle.classList.toggle('active');
                mobileNav.classList.toggle('active');
                
                if (mobileNav.classList.contains('active')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            });
            
            // Закрытие меню при клике на ссылки
            const navLinks = mobileNav.querySelectorAll('.nav__link:not(.theme-switcher)');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    mobileToggle.classList.remove('active');
                    mobileNav.classList.remove('active');
                    document.body.style.overflow = '';
                });
            });
        }
    }

    loadLogoUrls() {
        const logoElement = document.querySelector('.logo, #dynamic-logo');
        if (logoElement) {
            this.logos = {
                light: logoElement.dataset.lightLogo || logoElement.src,
                dark: logoElement.dataset.darkLogo || logoElement.src
            };
        }
    }

    updateLogo(theme) {
        const logoElement = document.querySelector('.logo, #dynamic-logo');
        if (logoElement && this.logos && this.logos[theme]) {
            logoElement.style.opacity = '0';
            setTimeout(() => {
                logoElement.src = this.logos[theme];
                logoElement.style.opacity = '1';
            }, 150);
        }
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === this.themes.dark ? this.themes.light : this.themes.dark;
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        this.applyTheme(theme, true);
    }

    applyTheme(theme, updateStorage = true) {
        const htmlElement = document.documentElement;
        const bodyElement = document.body;

        if (theme === this.themes.light) {
            htmlElement.classList.remove(this.DARK_THEME_CLASS);
            if (bodyElement) bodyElement.classList.remove(this.DARK_THEME_CLASS);
        } else {
            htmlElement.classList.add(this.DARK_THEME_CLASS);
            if (bodyElement) bodyElement.classList.add(this.DARK_THEME_CLASS);
        }

        if (updateStorage) {
            localStorage.setItem(this.STORAGE_KEY, theme);
            this.setCookie(this.COOKIE_KEY, theme, 365);
        }

        this.updateSwitcherUI(theme);
        this.updateLogo(theme);
    }

    updateSwitcherUI(theme) {
        const textElement = document.getElementById('theme-text');
        if (textElement) {
            textElement.textContent = theme === this.themes.dark ? 'Светлая тема' : 'Тёмная тема';
        }
    }

    getCurrentTheme() {
        const cookieTheme = this.getCookie(this.COOKIE_KEY);
        return cookieTheme || localStorage.getItem(this.STORAGE_KEY) || this.themes.light;
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }
}

// Глобальная инициализация
if (!window.themeManager) {
    window.themeManager = new ThemeManager();
}
