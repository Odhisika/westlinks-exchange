/**
 * Module Loader for CoinVibe Pay
 * Handles dynamic loading of ES6 modules and provides a simple API for module management
 */

class ModuleLoader {
    constructor() {
        this.modules = new Map();
        this.loaded = new Set();
    }

    async load(modulePath) {
        if (this.loaded.has(modulePath)) {
            return this.modules.get(modulePath);
        }

        try {
            const module = await import(modulePath);
            this.modules.set(modulePath, module);
            this.loaded.add(modulePath);
            return module;
        } catch (error) {
            console.error(`Failed to load module: ${modulePath}`, error);
            throw error;
        }
    }

    async loadMultiple(modulePaths) {
        const promises = modulePaths.map(path => this.load(path));
        return Promise.all(promises);
    }

    get(modulePath) {
        return this.modules.get(modulePath);
    }

    isLoaded(modulePath) {
        return this.loaded.has(modulePath);
    }
}

// Create global module loader instance
window.moduleLoader = new ModuleLoader();

// Helper function to initialize authentication system
window.initializeAuthSystem = async function() {
    try {
        const authModule = await window.moduleLoader.load('./components/auth/index.js');
        if (authModule.initializeAuth) {
            authModule.initializeAuth();
            console.log('Authentication system initialized successfully');
        }
    } catch (error) {
        console.error('Failed to initialize authentication system:', error);
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.initializeAuthSystem();
    });
} else {
    window.initializeAuthSystem();
}