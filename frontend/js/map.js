/**
 * Map Module - OpenLayers Map Initialization and Management
 */

// Using global ol object from CDN
const { Map, View } = ol;
const { Tile: TileLayer, Image: ImageLayer } = ol.layer;
const { OSM, ImageWMS } = ol.source;
const { fromLonLat } = ol.proj;

// Configuration
const WMS_URL = '/thredds/wms';  // Use nginx proxy instead of direct access
const INITIAL_CENTER = [0, 20];
const INITIAL_ZOOM = 3;
const MIN_ZOOM = 2;
const MAX_ZOOM = 15;

/**
 * Weather layer configuration for each parameter
 * Using THREDDS WMS endpoints
 */
const WEATHER_LAYERS = {
    temp_2m: {
        dataset: 'weather/temp_2m/temp_2m_2025102712.nc',
        layer: 't2m',
        title: 'Temperature at 2m (°C)',
        colorRange: '220,320',  // Data is in Kelvin
        palette: 'windy',       // High-contrast palette similar to Windy
        unit: 'K',
        gamma: '0.85'           // Increase contrast (lower than 1 = more contrast)
    },
    temp_850mb: {
        dataset: 'weather/temp_850mb/temp_850mb_2025102712.nc',
        layer: 't',
        title: 'Temperature at 850mb (°C)',
        colorRange: '220,310',  // Data is in Kelvin
        palette: 'default-scalar/default',
        unit: 'K'
    },
    wind_speed_10m: {
        dataset: 'weather/wind_speed_10m/wind_speed_10m_2025102712.nc',
        layer: 'wind_speed',
        title: 'Wind Speed at 10m (m/s)',
        colorRange: '0,30',
        palette: 'default-scalar/default',
        unit: 'm/s'
    },
    wind_speed_50m: {
        dataset: 'weather/wind_speed_50m/wind_speed_50m_2025102712.nc',
        layer: 'wind_speed',
        title: 'Wind Speed at 50m (m/s)',
        colorRange: '0,40',
        palette: 'default-scalar/default',
        unit: 'm/s'
    },
    precip_rate: {
        dataset: 'weather/precip_rate/precip_rate_2025102712.nc',
        layer: 'prate',
        title: 'Precipitation Rate (mm/hr)',
        colorRange: '0,10',
        palette: 'default-scalar/default',
        unit: 'mm/hr'
    },
    mslp: {
        dataset: 'weather/mslp/mslp_2025102712.nc',
        layer: 'prmsl',
        title: 'Mean Sea Level Pressure (hPa)',
        colorRange: '96000,104000',
        palette: 'default-scalar/default',
        unit: 'hPa'
    },
    rh_2m: {
        dataset: 'weather/rh_2m/rh_2m_2025102712.nc',
        layer: 'r2',
        title: 'Relative Humidity at 2m (%)',
        colorRange: '0,100',
        palette: 'default-scalar/default',
        unit: '%'
    }
};

/**
 * WeatherMap class - Manages the OpenLayers map and weather layers
 */
class WeatherMap {
    constructor(targetElementId) {
        this.targetElement = targetElementId;
        this.map = null;
        this.baseLayer = null;
        this.weatherLayer = null;
        this.currentParameter = 'temp_2m';
        this.currentTime = null;
        this.availableTimes = [];
        this.opacity = 0.9;
        
        this.init();
    }
    
    /**
     * Initialize the map with base layer
     */
    init() {
        // Create base layer (OpenStreetMap)
        this.baseLayer = new TileLayer({
            source: new OSM(),
            preload: 4
        });
        
        // Create map
        this.map = new Map({
            target: this.targetElement,
            layers: [this.baseLayer],
            view: new View({
                center: fromLonLat(INITIAL_CENTER),
                zoom: INITIAL_ZOOM,
                minZoom: MIN_ZOOM,
                maxZoom: MAX_ZOOM
            })
        });
        
        // Don't create weather layer yet - wait for times to be loaded
        // The weather layer will be created when updateTime() is first called
    }
    
    /**
     * Create weather layer with WMS source
     */
    createWeatherLayer() {
        const config = WEATHER_LAYERS[this.currentParameter];
        
        const wmsParams = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'LAYERS': config.layer,
            'FORMAT': 'image/png',
            'TRANSPARENT': true,
            'COLORSCALERANGE': config.colorRange,
            'NUMCOLORBANDS': 250,
            'STYLES': config.palette,
            'GAMMA': config.gamma || '0.85',
            'ABOVEMAXCOLOR': 'extend',
            'BELOWMINCOLOR': 'extend',
            'LOGSCALE': false
        };
        
        // Add time parameter if available
        if (this.currentTime) {
            wmsParams.TIME = this.currentTime;
        }
        
        // Construct dataset-specific WMS URL
        const datasetUrl = `${WMS_URL}/${config.dataset}`;
        
        const source = new ImageWMS({
            url: datasetUrl,
            params: wmsParams,
            ratio: 1,
            crossOrigin: 'anonymous'
        });
        
        // Remove existing weather layer if present
        if (this.weatherLayer) {
            this.map.removeLayer(this.weatherLayer);
        }
        
        // Create new weather layer
        this.weatherLayer = new ImageLayer({
            source: source,
            opacity: this.opacity,
            zIndex: 10
        });
        
        this.map.addLayer(this.weatherLayer);
    }
    
    /**
     * Update weather parameter
     * @param {string} parameter - Parameter ID
     */
    updateParameter(parameter) {
        if (this.currentParameter === parameter) return;
        
        this.currentParameter = parameter;
        this.createWeatherLayer();
    }
    
    /**
     * Update time dimension
     * @param {string} time - ISO 8601 timestamp
     */
    updateTime(time) {
        this.currentTime = time;
        
        // Create weather layer if it doesn't exist yet
        if (!this.weatherLayer) {
            this.createWeatherLayer();
            return;
        }
        
        // Update existing layer
        const source = this.weatherLayer.getSource();
        const params = source.getParams();
        params.TIME = time;
        source.updateParams(params);
        source.refresh();
    }
    
    /**
     * Set layer opacity
     * @param {number} opacity - Opacity value (0-1)
     */
    setOpacity(opacity) {
        this.opacity = opacity;
        if (this.weatherLayer) {
            this.weatherLayer.setOpacity(opacity);
        }
    }
    
    /**
     * Toggle weather layer visibility
     * @param {boolean} visible - Show or hide layer
     */
    setLayerVisible(visible) {
        if (this.weatherLayer) {
            this.weatherLayer.setVisible(visible);
        }
    }
    
    /**
     * Get current parameter configuration
     * @returns {object} Parameter configuration
     */
    getCurrentParameterConfig() {
        return WEATHER_LAYERS[this.currentParameter];
    }
    
    /**
     * Get legend URL for current parameter
     * @returns {string} Legend image URL
     */
    getLegendUrl() {
        const config = WEATHER_LAYERS[this.currentParameter];
        const datasetUrl = `${WMS_URL}/${config.dataset}`;
        
        // THREDDS ncWMS uses GetMetadata for legend generation
        const params = new URLSearchParams({
            'REQUEST': 'GetMetadata',
            'item': 'legend',
            'LAYERS': config.layer,
            'STYLES': config.palette,
            'COLORSCALERANGE': config.colorRange,
            'NUMCOLORBANDS': '250',
            'VERTICAL': 'true',
            'WIDTH': '2',
            'HEIGHT': '200'
        });
        
        return `${datasetUrl}?${params.toString()}`;
    }
    
    /**
     * Fetch available times from WMS GetCapabilities
     * @returns {Promise<Array<string>>} Array of ISO 8601 timestamps
     */
    async fetchAvailableTimes() {
        try {
            // Use the first dataset to get time dimension
            const config = WEATHER_LAYERS[this.currentParameter];
            const datasetUrl = `${WMS_URL}/${config.dataset}`;
            
            const params = new URLSearchParams({
                'SERVICE': 'WMS',
                'REQUEST': 'GetCapabilities',
                'VERSION': '1.3.0'
            });
            
            const response = await fetch(`${datasetUrl}?${params.toString()}`);
            const text = await response.text();
            
            // Parse XML to extract time dimension
            const parser = new DOMParser();
            const xml = parser.parseFromString(text, 'text/xml');
            
            // Find Dimension element with name="time"
            const dimensions = xml.getElementsByTagName('Dimension');
            for (let dim of dimensions) {
                if (dim.getAttribute('name') === 'time') {
                    const timeString = dim.textContent.trim();
                    
                    // Handle ISO 8601 interval format (start/end/period)
                    if (timeString.includes('/')) {
                        const parts = timeString.split('/');
                        if (parts.length === 3) {
                            // Parse start, end, and period
                            const start = new Date(parts[0]);
                            const end = new Date(parts[1]);
                            const period = parts[2]; // PT3H format
                            
                            // Extract hours from period (e.g., PT3H = 3 hours)
                            const hours = parseInt(period.match(/PT(\d+)H/)[1]);
                            
                            // Generate time steps
                            const times = [];
                            let current = new Date(start);
                            while (current <= end) {
                                times.push(current.toISOString());
                                current = new Date(current.getTime() + hours * 60 * 60 * 1000);
                            }
                            
                            this.availableTimes = times;
                            return this.availableTimes;
                        }
                    }
                    
                    // Fallback: Parse comma-separated values
                    const times = timeString.split(',').map(t => t.trim());
                    this.availableTimes = times.sort();
                    return this.availableTimes;
                }
            }
            
            return [];
        } catch (error) {
            console.error('Error fetching available times:', error);
            return [];
        }
    }
    
    /**
     * Get value at specific coordinate (GetFeatureInfo)
     * @param {Array<number>} coordinate - [lon, lat]
     * @returns {Promise<object>} Feature info response
     */
    async getValueAtCoordinate(coordinate) {
        if (!this.weatherLayer || !this.currentTime) return null;
        
        try {
            const view = this.map.getView();
            const resolution = view.getResolution();
            const projection = view.getProjection();
            
            const url = this.weatherLayer.getSource().getFeatureInfoUrl(
                coordinate,
                resolution,
                projection,
                {
                    'INFO_FORMAT': 'application/json',
                    'QUERY_LAYERS': WEATHER_LAYERS[this.currentParameter].layer,
                    'TIME': this.currentTime
                }
            );
            
            if (url) {
                const response = await fetch(url);
                const data = await response.json();
                return data;
            }
            
            return null;
        } catch (error) {
            console.error('Error getting feature info:', error);
            return null;
        }
    }
    
    /**
     * Get the OpenLayers map instance
     * @returns {Map} OpenLayers map
     */
    getMap() {
        return this.map;
    }
}
