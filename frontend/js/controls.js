/**
 * Controls Module - Handles UI interactions and user input
 */

/**
 * WeatherControls class - Manages UI controls and event handlers
 */
class WeatherControls {
    constructor(weatherMap, animation) {
        this.weatherMap = weatherMap;
        this.animation = animation;
        
        this.elements = {
            // Parameter selection
            weatherParam: document.getElementById('weatherParam'),
            
            // Layer controls
            layerToggle: document.getElementById('layerToggle'),
            opacitySlider: document.getElementById('opacitySlider'),
            opacityValue: document.getElementById('opacityValue'),
            
            // Animation controls
            playPauseBtn: document.getElementById('playPauseBtn'),
            playPauseIcon: document.getElementById('playPauseIcon'),
            stopBtn: document.getElementById('stopBtn'),
            speedButtons: document.querySelectorAll('.btn-speed'),
            timelineSlider: document.getElementById('timelineSlider'),
            currentTime: document.getElementById('currentTime'),
            
            // Legend
            legendImage: document.getElementById('legendImage'),
            legendMin: document.getElementById('legendMin'),
            legendMax: document.getElementById('legendMax'),
            
            // Value display
            valueDisplay: document.getElementById('valueDisplay'),
            
            // Theme toggle
            themeToggle: document.getElementById('themeToggle'),
            
            // Loading indicator
            loading: document.getElementById('loading'),
            statusMessage: document.getElementById('statusMessage')
        };
        
        this.debounceTimer = null;
        this.init();
    }
    
    /**
     * Initialize all event listeners
     */
    init() {
        // Weather parameter selection
        this.elements.weatherParam.addEventListener('change', (e) => {
            this.handleParameterChange(e.target.value);
        });
        
        // Layer toggle
        this.elements.layerToggle.addEventListener('change', (e) => {
            this.weatherMap.setLayerVisible(e.target.checked);
        });
        
        // Opacity control
        this.elements.opacitySlider.addEventListener('input', (e) => {
            const opacity = e.target.value / 100;
            this.weatherMap.setOpacity(opacity);
            this.elements.opacityValue.textContent = `${e.target.value}%`;
        });
        
        // Play/Pause button
        this.elements.playPauseBtn.addEventListener('click', () => {
            this.togglePlayPause();
        });
        
        // Stop button
        this.elements.stopBtn.addEventListener('click', () => {
            this.animation.stop();
            this.updateAnimationUI();
        });
        
        // Speed buttons
        this.elements.speedButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const speed = parseFloat(e.target.dataset.speed);
                this.setSpeed(speed);
            });
        });
        
        // Timeline slider
        this.elements.timelineSlider.addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.animation.goToFrame(index);
            this.updateTimeDisplay();
        });
        
        // Theme toggle
        this.elements.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });
        
        // Map hover for value display
        this.weatherMap.getMap().on('pointermove', (evt) => {
            this.handleMapHover(evt);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
        
        // Update animation UI periodically
        setInterval(() => {
            if (this.animation.getIsPlaying()) {
                this.updateAnimationUI();
            }
        }, 100);
    }
    
    /**
     * Handle weather parameter change
     * @param {string} parameter - New parameter ID
     */
    handleParameterChange(parameter) {
        this.showLoading();
        this.weatherMap.updateParameter(parameter);
        this.updateLegend();
        setTimeout(() => this.hideLoading(), 500);
    }
    
    /**
     * Toggle play/pause state
     */
    togglePlayPause() {
        if (this.animation.getIsPlaying()) {
            this.animation.pause();
        } else {
            this.animation.play();
        }
        this.updateAnimationUI();
    }
    
    /**
     * Set animation speed
     * @param {number} speed - Speed multiplier
     */
    setSpeed(speed) {
        this.animation.setSpeed(speed);
        
        // Update active button
        this.elements.speedButtons.forEach(btn => {
            const btnSpeed = parseFloat(btn.dataset.speed);
            if (btnSpeed === speed) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    /**
     * Update animation UI (play button, timeline, time display)
     */
    updateAnimationUI() {
        const isPlaying = this.animation.getIsPlaying();
        
        // Update play/pause button
        this.elements.playPauseIcon.textContent = isPlaying ? '⏸' : '▶';
        this.elements.playPauseBtn.innerHTML = `<span id="playPauseIcon">${isPlaying ? '⏸' : '▶'}</span> ${isPlaying ? 'Pause' : 'Play'}`;
        
        // Update timeline slider
        const currentIndex = this.animation.getCurrentIndex();
        this.elements.timelineSlider.value = currentIndex;
        
        // Update time display
        this.updateTimeDisplay();
    }
    
    /**
     * Update time display text
     */
    updateTimeDisplay() {
        const currentTime = this.animation.getCurrentTime();
        this.elements.currentTime.textContent = WeatherAnimation.formatTime(currentTime);
    }
    
    /**
     * Update legend image and labels
     */
    updateLegend() {
        const legendUrl = this.weatherMap.getLegendUrl();
        this.elements.legendImage.src = legendUrl;
        
        const config = this.weatherMap.getCurrentParameterConfig();
        const [min, max] = config.colorRange.split(',');
        
        this.elements.legendMin.textContent = `${min} ${config.unit}`;
        this.elements.legendMax.textContent = `${max} ${config.unit}`;
    }
    
    /**
     * Handle map hover for value display
     * @param {Object} event - OpenLayers map event
     */
    handleMapHover(event) {
        // Temporarily disabled due to THREDDS GetFeatureInfo compatibility issues
        // The weather visualization still works perfectly without hover values
        this.hideHoverValue();
    }
    
    /**
     * Show hover value display
     * @param {number} value - Value to display
     */
    showHoverValue(value) {
        this.elements.valueDisplay.textContent = `Value: ${value.toFixed(2)}`;
        this.elements.valueDisplay.classList.remove('hidden');
    }
    
    /**
     * Hide hover value display
     */
    hideHoverValue() {
        this.elements.valueDisplay.classList.add('hidden');
    }
    
    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyboard(e) {
        // Space: toggle play/pause
        if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
            e.preventDefault();
            this.togglePlayPause();
        }
        
        // Arrow left: previous frame
        if (e.code === 'ArrowLeft') {
            e.preventDefault();
            this.animation.previousFrame();
            this.updateAnimationUI();
        }
        
        // Arrow right: next frame
        if (e.code === 'ArrowRight') {
            e.preventDefault();
            this.animation.nextFrame();
            this.updateAnimationUI();
        }
        
        // Escape: stop animation
        if (e.code === 'Escape') {
            this.animation.stop();
            this.updateAnimationUI();
        }
    }
    
    /**
     * Toggle dark theme
     */
    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        
        // Update theme icon
        const icon = this.elements.themeToggle.querySelector('.icon');
        icon.textContent = isDark ? '☀️' : '🌙';
        
        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
    
    /**
     * Load saved theme preference
     */
    loadThemePreference() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            const icon = this.elements.themeToggle.querySelector('.icon');
            icon.textContent = '☀️';
        }
    }
    
    /**
     * Initialize timeline with available times
     * @param {Array<string>} times - Array of ISO 8601 timestamps
     */
    initTimeline(times) {
        this.animation.setTimes(times);
        this.elements.timelineSlider.max = times.length - 1;
        this.elements.timelineSlider.value = 0;
        this.updateTimeDisplay();
        this.updateLegend();
    }
    
    /**
     * Show loading indicator
     */
    showLoading() {
        this.elements.loading.classList.remove('hidden');
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        this.elements.loading.classList.add('hidden');
    }
    
    /**
     * Show status message
     * @param {string} message - Message text
     * @param {string} type - Message type ('success', 'error', 'warning')
     */
    showStatus(message, type = 'success') {
        this.elements.statusMessage.textContent = message;
        this.elements.statusMessage.className = `status-message ${type}`;
        this.elements.statusMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.elements.statusMessage.classList.add('hidden');
        }, 5000);
    }
    
    /**
     * Hide status message
     */
    hideStatus() {
        this.elements.statusMessage.classList.add('hidden');
    }
}
