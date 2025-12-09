/**
 * Integration Script for Modular Components
 * This script helps integrate the new modular authentication system with the existing index.html
 */

// Global API URL configuration
window.API_URL = window.API_URL || 'http://localhost:8000/api';

// Simple module loader for browsers that don't support ES6 modules
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Initialize modular authentication system
async function initializeModularAuth() {
    try {
        console.log('Initializing modular authentication system...');
        
        // Load required modules
        await loadScript('./components/ui-components.js');
        
        // Create a simple auth manager if ES6 modules aren't available
        if (!window.LoginModal) {
            console.log('Creating fallback authentication system...');
            createFallbackAuthSystem();
        } else {
            console.log('Using ES6 modular authentication system');
            // ES6 modules will be loaded via the module-loader.js script
        }
        
        console.log('✓ Authentication system initialized');
    } catch (error) {
        console.error('Failed to initialize modular authentication:', error);
        // Create fallback system
        createFallbackAuthSystem();
    }
}

// Fallback authentication system for browsers without ES6 module support
function createFallbackAuthSystem() {
    // Store references to original functions
    window.originalShowLogin = window.showLogin;
    window.originalShowRegister = window.showRegister;
    window.originalSubmitLogin = window.submitLogin;
    window.originalSubmitRegister = window.submitRegister;
    
    // Enhanced login function with better error handling
    window.showLogin = function() {
        try {
            const modal = document.getElementById('loginModal');
            const content = document.getElementById('loginModalContent');
            
            if (!modal || !content) {
                console.error('Login modal elements not found');
                return;
            }
            
            modal.classList.remove('hidden');
            // Animate in
            setTimeout(() => {
                content.classList.remove('scale-95', 'opacity-0');
                content.classList.add('scale-100', 'opacity-100');
            }, 10);
            
            console.log('✓ Login modal opened (fallback)');
        } catch (error) {
            console.error('Error opening login modal:', error);
        }
    };
    
    // Enhanced register function with better error handling
    window.showRegister = function() {
        try {
            const modal = document.getElementById('registerModal');
            const content = document.getElementById('registerModalContent');
            
            if (!modal || !content) {
                console.error('Register modal elements not found');
                return;
            }
            
            modal.classList.remove('hidden');
            // Animate in
            setTimeout(() => {
                content.classList.remove('scale-95', 'opacity-0');
                content.classList.add('scale-100', 'opacity-100');
            }, 10);
            
            console.log('✓ Register modal opened (fallback)');
        } catch (error) {
            console.error('Error opening register modal:', error);
        }
    };
    
    // Enhanced close modal function
    window.closeModal = function(modalId) {
        try {
            const modal = document.getElementById(modalId);
            if (!modal) {
                console.warn(`Modal ${modalId} not found`);
                return;
            }
            
            const content = modal.querySelector('[id*="Content"]');
            if (content) {
                content.classList.add('scale-95', 'opacity-0');
                content.classList.remove('scale-100', 'opacity-100');
                
                setTimeout(() => {
                    modal.classList.add('hidden');
                }, 300);
            } else {
                modal.classList.add('hidden');
            }
            
            console.log(`✓ Modal ${modalId} closed`);
        } catch (error) {
            console.error('Error closing modal:', error);
        }
    };
    
    console.log('✓ Fallback authentication system created');
}

// Enhanced password strength checker
function checkPasswordStrength(password) {
    try {
        const strengthBar = document.getElementById('strengthBar');
        const strengthText = document.getElementById('strengthText');
        const strengthDiv = document.getElementById('passwordStrength');
        
        if (!strengthBar || !strengthText || !strengthDiv) {
            console.warn('Password strength elements not found');
            return;
        }
        
        if (password.length === 0) {
            strengthDiv.classList.add('hidden');
            return;
        }
        
        strengthDiv.classList.remove('hidden');
        
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        
        const strengthPercent = (strength / 5) * 100;
        const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const strengthColors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981'];
        
        strengthBar.style.width = strengthPercent + '%';
        strengthText.textContent = strengthLabels[strength - 1] || 'Very Weak';
        strengthText.style.color = strengthColors[strength - 1] || '#ef4444';
        strengthBar.style.backgroundColor = strengthColors[strength - 1] || '#ef4444';
        
        console.log(`✓ Password strength checked: ${strengthLabels[strength - 1]}`);
    } catch (error) {
        console.error('Error checking password strength:', error);
    }
}

// Enhanced login submission with better error handling
async function submitLogin(e) {
    if (e) e.preventDefault();
    
    try {
        const email = document.getElementById('loginEmail')?.value.trim();
        const password = document.getElementById('loginPassword')?.value;
        const errDiv = document.getElementById('loginError');
        const errText = document.getElementById('loginErrorText');
        
        if (!email || !password) {
            if (errDiv && errText) {
                errText.textContent = 'Please fill in all fields';
                errDiv.classList.remove('hidden');
            }
            return;
        }
        
        if (errDiv) errDiv.classList.add('hidden');
        
        const res = await fetch(`${API_URL}/vendors/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        
        if (data.success) {
            localStorage.setItem('coinvibe_token', data.token);
            localStorage.setItem('coinvibe_user', JSON.stringify(data.vendor));
            closeModal('loginModal');
            
            if (window.updateAuthUI) {
                window.updateAuthUI();
            }
            
            window.location.href = 'dashboard.html';
            console.log('✓ Login successful');
        } else {
            if (errDiv && errText) {
                errText.textContent = data.detail || 'Login failed. Please check your credentials.';
                errDiv.classList.remove('hidden');
            }
            console.warn('✗ Login failed:', data.detail);
        }
    } catch (error) {
        console.error('Login error:', error);
        const errDiv = document.getElementById('loginError');
        const errText = document.getElementById('loginErrorText');
        if (errDiv && errText) {
            errText.textContent = 'An unexpected error occurred. Please try again.';
            errDiv.classList.remove('hidden');
        }
    }
}

// Enhanced register submission with better validation
async function submitRegister(e) {
    if (e) e.preventDefault();
    
    try {
        const name = document.getElementById('regName')?.value.trim();
        const email = document.getElementById('regEmail')?.value.trim();
        const password = document.getElementById('regPassword')?.value;
        const momo = document.getElementById('regMomo')?.value.trim();
        const country = document.getElementById('regCountry')?.value.trim();
        const errDiv = document.getElementById('regError');
        const errText = document.getElementById('regErrorText');
        
        if (!name || !email || !password || !momo || !country) {
            if (errDiv && errText) {
                errText.textContent = 'Please fill in all fields';
                errDiv.classList.remove('hidden');
            }
            return;
        }
        
        if (!passwordStrong(password)) {
            if (errDiv && errText) {
                errText.textContent = 'Password must be at least 8 characters with uppercase, lowercase, number and special character.';
                errDiv.classList.remove('hidden');
            }
            return;
        }
        
        if (errDiv) errDiv.classList.add('hidden');
        
        const res = await fetch(`${API_URL}/vendors/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, momo_number: momo, country })
        });
        
        const data = await res.json();
        
        if (data.success) {
            // Auto-login after successful registration
            const loginRes = await fetch(`${API_URL}/vendors/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const loginData = await loginRes.json();
            if (loginData.success) {
                localStorage.setItem('coinvibe_token', loginData.token);
                localStorage.setItem('coinvibe_user', JSON.stringify(loginData.vendor));
                closeModal('registerModal');
                
                if (window.updateAuthUI) {
                    window.updateAuthUI();
                }
                
                window.location.href = 'dashboard.html';
                console.log('✓ Registration and auto-login successful');
            } else {
                if (errDiv && errText) {
                    errText.textContent = loginData.detail || 'Auto-login failed. Please try logging in manually.';
                    errDiv.classList.remove('hidden');
                }
                console.warn('✗ Auto-login failed:', loginData.detail);
            }
        } else {
            if (errDiv && errText) {
                errText.textContent = data.detail || 'Registration failed. Please try again.';
                errDiv.classList.remove('hidden');
            }
            console.warn('✗ Registration failed:', data.detail);
        }
    } catch (error) {
        console.error('Registration error:', error);
        const errDiv = document.getElementById('regError');
        const errText = document.getElementById('regErrorText');
        if (errDiv && errText) {
            errText.textContent = 'An unexpected error occurred. Please try again.';
            errDiv.classList.remove('hidden');
        }
    }
}

// Password strength validation function
function passwordStrong(pw) {
    return /[a-z]/.test(pw) && /[A-Z]/.test(pw) && /\d/.test(pw) && /[^A-Za-z0-9]/.test(pw) && pw.length >= 8;
}

// Initialize the system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing modular auth integration...');
    
    // Set up password strength checker
    const regPasswordInput = document.getElementById('regPassword');
    if (regPasswordInput) {
        regPasswordInput.addEventListener('input', function(e) {
            checkPasswordStrength(e.target.value);
        });
        console.log('✓ Password strength checker initialized');
    }
    
    // Set up form submissions
    const loginForm = document.querySelector('#loginModal form');
    if (loginForm) {
        loginForm.addEventListener('submit', submitLogin);
        console.log('✓ Login form handler attached');
    }
    
    const registerForm = document.querySelector('#registerModal form');
    if (registerForm) {
        registerForm.addEventListener('submit', submitRegister);
        console.log('✓ Register form handler attached');
    }
    
    // Initialize the modular system
    initializeModularAuth();
    
    console.log('✓ Modular authentication integration complete');
});

// Export functions for global use
window.submitLogin = submitLogin;
window.submitRegister = submitRegister;
window.checkPasswordStrength = checkPasswordStrength;
window.passwordStrong = passwordStrong;