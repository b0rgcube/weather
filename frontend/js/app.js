/**
 * Weather Visualization System - Main Application
 * Initializes and coordinates all modules
 * Note: This must be loaded after map.js, animation.js, and controls.js
 */

/**
 * Main Application Class
 */
class WeatherApp {
    constructor() {
        this.weatherMap = null;
        this.animation = null;
        this.controls = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Weather Visualization System...');
        
        try {
            // Show loading indicator
            this.showInitialLoading();
            
            // Initialize map
            this.weatherMap = new WeatherMap('map');
            console.log('Map initialized');
            
            // Initialize animation
            this.animation = new WeatherAnimation(this.weatherMap);
            console.log('Animation system initialized');
            
            // Initialize controls
            this.controls = new WeatherControls(this.weatherMap, this.animation);
            console.log('Controls initialized');
            
            // Load theme preference
            this.controls.loadThemePreference();
            
            // Fetch available times and initialize timeline
            await this.loadWeatherData();
            
            // Hide loading indicator
            this.hideInitialLoading();
            
            console.log('Weather Visualization System ready');
        } catch (error) {
            console.error('Error initializing application:', error);
            this.handleInitError(error);
        }
    }
    
    /**
     * Load weather data and initialize timeline
     */
    async loadWeatherData() {
        try {
            console.log('Fetching available forecast times...');
            const times = await this.weatherMap.fetchAvailableTimes();
            
            if (times.length === 0) {
                throw new Error('No weather data available. Data may still be downloading.');
            }
            
            console.log(`Found ${times.length} forecast time steps`);
            
            // Initialize timeline with fetched times
            this.controls.initTimeline(times);
            
            // Set initial time and update map
            if (times.length > 0) {
                this.animation.goToFrame(0);
            }
            
            this.controls.showStatus(
                `Loaded ${times.length} forecast time steps`,
                'success'
            );
            
            return times;
        } catch (error) {
            console.error('Error loading weather data:', error);
            
            // Retry logic
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying... (${this.retryCount}/${this.maxRetries})`);
                
                this.controls.showStatus(
                    `Loading data... Retry ${this.retryCount}/${this.maxRetries}`,
                    'warning'
                );
                
                // Wait 5 seconds before retry
                await new Promise(resolve => setTimeout(resolve, 5000));
                return this.loadWeatherData();
            } else {
                throw new Error('Failed to load weather data after multiple attempts. Please ensure the data fetcher service is running and data is available.');
            }
        }
    }
    
    /**
     * Show initial loading screen
     */
    showInitialLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.remove('hidden');
        }
    }
    
    /**
     * Hide initial loading screen
     */
    hideInitialLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.add('hidden');
        }
    }
    
    /**
     * Handle initialization error
     * @param {Error} error - Error object
     */
    handleInitError(error) {
        console.error('Fatal initialization error:', error);
        
        const loading = document.getElementById('loading');
        if (loading) {
            loading.innerHTML = `
                <div class="spinner" style="border-top-color: #F44336;"></div>
                <p style="color: #F44336;">
                    <strong>Error initializing application</strong><br>
                    ${error.message}
                </p>
                <p style="font-size: 0.75rem; color: #666;">
                    Please check that:<br>
                    • Docker services are running (docker-compose up)<br>
                    • GeoServer is accessible at http://localhost:8080<br>
                    • Weather data has been downloaded<br>
                    • Your browser console for more details
                </p>
                <button onclick="location.reload()" class="btn-primary" style="margin-top: 1rem;">
                    Retry
                </button>
            `;
        }
        
        if (this.controls) {
            this.controls.showStatus(error.message, 'error');
        }
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.weatherApp = new WeatherApp();
    });
} else {
    window.weatherApp = new WeatherApp();
}
