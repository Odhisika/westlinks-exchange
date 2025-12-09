// Modular Authentication System for CoinVibe Pay
// This file contains the modular authentication components

// API Configuration
const API_URL = 'http://localhost:8000/api';

// Authentication Manager
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.token = null;
        this.loadAuthState();
    }

    loadAuthState() {
        this.token = localStorage.getItem('coinvibe_token');
        const userData = localStorage.getItem('coinvibe_user');
        if (userData) {
            this.currentUser = JSON.parse(userData);
        }
    }

    saveAuthState(token, user) {
        this.token = token;
        this.currentUser = user;
        localStorage.setItem('coinvibe_token', token);
        localStorage.setItem('coinvibe_user', JSON.stringify(user));
    }

    clearAuthState() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('coinvibe_token');
        localStorage.removeItem('coinvibe_user');
    }

    isAuthenticated() {
        return !!this.token && !!this.currentUser;
    }

    async login(email, password) {
        try {
            const response = await fetch(`${API_URL}/vendors/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (data.success) {
                this.saveAuthState(data.token, data.vendor);
                return { success: true, user: data.vendor };
            } else {
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: error.message || 'Network error' };
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${API_URL}/vendors/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (data.success) {
                // Auto-login after registration
                return await this.login(userData.email, userData.password);
            } else {
                return { success: false, error: data.detail || 'Registration failed' };
            }
        } catch (error) {
            return { success: false, error: error.message || 'Network error' };
        }
    }

    logout() {
        this.clearAuthState();
        window.location.href = 'index.html';
    }

    updateUI() {
        const authButtons = document.getElementById('authButtons');
        const userMenu = document.getElementById('userMenu');
        const userNameElement = document.getElementById('userName');

        if (this.isAuthenticated()) {
            authButtons?.classList.add('hidden');
            userMenu?.classList.remove('hidden');
            if (userNameElement) {
                userNameElement.textContent = this.currentUser.name;
            }
        } else {
            userMenu?.classList.add('hidden');
            authButtons?.classList.remove('hidden');
            if (userNameElement) {
                userNameElement.textContent = '';
            }
        }
    }
}

// Modal Manager
class ModalManager {
    constructor() {
        this.activeModal = null;
        this.modals = {};
    }

    registerModal(name, modalElement) {
        this.modals[name] = modalElement;
    }

    showModal(name) {
        if (this.activeModal) {
            this.hideModal(this.activeModal);
        }

        const modal = this.modals[name];
        if (modal) {
            modal.classList.remove('hidden');
            const content = modal.querySelector('[id*="Content"]');
            if (content) {
                setTimeout(() => {
                    content.classList.remove('scale-95', 'opacity-0');
                    content.classList.add('scale-100', 'opacity-100');
                }, 10);
            }
            this.activeModal = name;
        }
    }

    hideModal(name) {
        const modal = this.modals[name];
        if (modal) {
            const content = modal.querySelector('[id*="Content"]');
            if (content) {
                content.classList.remove('scale-100', 'opacity-100');
                content.classList.add('scale-95', 'opacity-0');
            }
            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300);
        }
        if (this.activeModal === name) {
            this.activeModal = null;
        }
    }

    hideActiveModal() {
        if (this.activeModal) {
            this.hideModal(this.activeModal);
        }
    }
}

// Password Strength Checker
class PasswordStrengthChecker {
    static check(password) {
        let strength = 0;
        const requirements = [];

        if (password.length >= 8) {
            strength++;
        } else {
            requirements.push('minimum 8 characters');
        }

        if (/[a-z]/.test(password)) {
            strength++;
        } else {
            requirements.push('lowercase letter');
        }

        if (/[A-Z]/.test(password)) {
            strength++;
        } else {
            requirements.push('uppercase letter');
        }

        if (/\d/.test(password)) {
            strength++;
        } else {
            requirements.push('number');
        }

        if (/[^A-Za-z0-9]/.test(password)) {
            strength++;
        } else {
            requirements.push('special character');
        }

        const strengthPercent = (strength / 5) * 100;
        let strengthLabel = 'Weak';
        let strengthColor = 'red';

        if (strength === 5) {
            strengthLabel = 'Very Strong';
            strengthColor = 'green';
        } else if (strength >= 4) {
            strengthLabel = 'Strong';
            strengthColor = 'blue';
        } else if (strength >= 3) {
            strengthLabel = 'Medium';
            strengthColor = 'yellow';
        }

        return {
            strength,
            strengthPercent,
            strengthLabel,
            strengthColor,
            requirements,
            isStrong: strength >= 4
        };
    }

    static updateUI(password, barElement, textElement) {
        const check = this.check(password);
        
        if (barElement) {
            barElement.style.width = check.strengthPercent + '%';
            barElement.className = `h-1 rounded-full transition-all duration-300 bg-${check.strengthColor}-500`;
        }

        if (textElement) {
            textElement.textContent = check.strengthLabel;
            textElement.className = `font-semibold text-${check.strengthColor}-500`;
        }

        return check;
    }
}

// Form Validator
class FormValidator {
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validatePhoneNumber(phone) {
        const phoneRegex = /^\+?[0-9]{10,15}$/;
        return phoneRegex.test(phone.replace(/\s/g, ''));
    }

    static validatePassword(password) {
        return PasswordStrengthChecker.check(password).isStrong;
    }

    static showError(element, message) {
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        }
    }

    static hideError(element) {
        if (element) {
            element.classList.add('hidden');
        }
    }
}

// Initialize global instances
window.AuthManager = new AuthManager();
window.ModalManager = new ModalManager();

// Utility functions
window.AuthUtils = {
    togglePassword: function(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.type = input.type === 'password' ? 'text' : 'password';
        }
    },

    showLoginModal: function() {
        window.ModalManager.showModal('loginModal');
    },

    showRegisterModal: function() {
        window.ModalManager.showModal('registerModal');
    },

    closeModal: function(modalId) {
        window.ModalManager.hideModal(modalId);
    },

    logout: function() {
        window.AuthManager.logout();
    }
};

// Initialize authentication system
document.addEventListener('DOMContentLoaded', function() {
    // Register modals
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    
    if (loginModal) {
        window.ModalManager.registerModal('loginModal', loginModal);
    }
    
    if (registerModal) {
        window.ModalManager.registerModal('registerModal', registerModal);
    }

    // Update UI based on authentication state
    window.AuthManager.updateUI();

    console.log('Authentication system initialized');
});