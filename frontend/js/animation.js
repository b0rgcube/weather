/**
 * Animation Module - Handles weather data time animation
 */

/**
 * WeatherAnimation class - Manages animation playback and timing
 */
class WeatherAnimation {
    constructor(weatherMap) {
        this.weatherMap = weatherMap;
        this.isPlaying = false;
        this.currentIndex = 0;
        this.speed = 1; // Animation speed multiplier (0.5x, 1x, 2x, 4x)
        this.baseInterval = 1000; // 1 second base frame rate
        this.animationInterval = null;
        this.times = [];
        this.loopEnabled = true;
    }
    
    /**
     * Set available times for animation
     * @param {Array<string>} times - Array of ISO 8601 timestamps
     */
    setTimes(times) {
        this.times = times;
        this.currentIndex = 0;
    }
    
    /**
     * Start animation playback
     */
    play() {
        if (this.isPlaying || this.times.length === 0) return;
        
        this.isPlaying = true;
        const interval = this.baseInterval / this.speed;
        
        this.animationInterval = setInterval(() => {
            this.nextFrame();
        }, interval);
    }
    
    /**
     * Pause animation playback
     */
    pause() {
        this.isPlaying = false;
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }
    }
    
    /**
     * Stop animation and reset to first frame
     */
    stop() {
        this.pause();
        this.currentIndex = 0;
        this.updateMap();
    }
    
    /**
     * Move to next frame in animation
     */
    nextFrame() {
        if (this.times.length === 0) return;
        
        this.currentIndex++;
        
        // Loop back to start if enabled
        if (this.currentIndex >= this.times.length) {
            if (this.loopEnabled) {
                this.currentIndex = 0;
            } else {
                this.pause();
                this.currentIndex = this.times.length - 1;
                return;
            }
        }
        
        this.updateMap();
    }
    
    /**
     * Move to previous frame in animation
     */
    previousFrame() {
        if (this.times.length === 0) return;
        
        this.currentIndex--;
        
        if (this.currentIndex < 0) {
            this.currentIndex = this.times.length - 1;
        }
        
        this.updateMap();
    }
    
    /**
     * Set animation speed multiplier
     * @param {number} speed - Speed multiplier (0.5, 1, 2, 4)
     */
    setSpeed(speed) {
        const wasPlaying = this.isPlaying;
        
        if (wasPlaying) {
            this.pause();
        }
        
        this.speed = speed;
        
        if (wasPlaying) {
            this.play();
        }
    }
    
    /**
     * Go to specific frame index
     * @param {number} index - Frame index
     */
    goToFrame(index) {
        if (index < 0 || index >= this.times.length) return;
        
        this.currentIndex = index;
        this.updateMap();
    }
    
    /**
     * Update map with current time
     */
    updateMap() {
        if (this.times.length === 0 || this.currentIndex >= this.times.length) return;
        
        const currentTime = this.times[this.currentIndex];
        this.weatherMap.updateTime(currentTime);
    }
    
    /**
     * Get current time string
     * @returns {string} Current ISO 8601 timestamp
     */
    getCurrentTime() {
        if (this.times.length === 0 || this.currentIndex >= this.times.length) {
            return null;
        }
        return this.times[this.currentIndex];
    }
    
    /**
     * Get current frame index
     * @returns {number} Current frame index
     */
    getCurrentIndex() {
        return this.currentIndex;
    }
    
    /**
     * Get total number of frames
     * @returns {number} Total frame count
     */
    getTotalFrames() {
        return this.times.length;
    }
    
    /**
     * Check if animation is playing
     * @returns {boolean} Playing state
     */
    getIsPlaying() {
        return this.isPlaying;
    }
    
    /**
     * Format time string for display
     * @param {string} isoTime - ISO 8601 timestamp
     * @returns {string} Formatted time string
     */
    static formatTime(isoTime) {
        if (!isoTime) return '--';
        
        try {
            const date = new Date(isoTime);
            
            // Format: "Oct 27, 2025 12:00 UTC"
            const options = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'UTC',
                timeZoneName: 'short'
            };
            
            return date.toLocaleString('en-US', options);
        } catch (error) {
            console.error('Error formatting time:', error);
            return isoTime;
        }
    }
    
    /**
     * Enable or disable animation looping
     * @param {boolean} enabled - Loop enabled state
     */
    setLoopEnabled(enabled) {
        this.loopEnabled = enabled;
    }
}
