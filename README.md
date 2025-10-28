# Weather Visualization System

A comprehensive weather visualization system that displays animated weather data overlays on an OpenLayers map, powered by NOAA GFS forecast data.

![Weather Visualization System](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 🗺️ **Interactive Map**: OpenLayers-based map with OpenStreetMap base layer
- 🌡️ **Multiple Weather Parameters**: Temperature, wind speed, precipitation, pressure, humidity
- 🎬 **Smooth Animation**: Playback controls with adjustable speed (0.5x - 4x)
- 📊 **Real-time Legend**: Dynamic color scales for each parameter
- 🎨 **Dark Mode**: Built-in dark theme support
- 📱 **Responsive Design**: Works on desktop and tablet devices
- ⌨️ **Keyboard Shortcuts**: Space to play/pause, arrows to navigate frames
- 🔍 **Value on Hover**: Display weather values at cursor position
- 🔄 **Auto-refresh**: Automatic data downloads every 6 hours

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Nginx)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   HTML/CSS  │  │  JavaScript  │  │   OpenLayers   │ │
│  │             │  │   Modules    │  │      Map       │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│          THREDDS Data Server (Port 8080)                 │
│  • WMS - Map visualization                              │
│  • OPeNDAP - Direct data access                         │
│  • NetCDF Subset Service                                │
│  • WCS - Coverage service                               │
│  • Industry-standard for atmospheric data               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Data Fetcher Service (Python)               │
│  • Downloads NOAA GFS GRIB2 data                        │
│  • Converts to NetCDF format                            │
│  • Runs every 6 hours                                   │
│  • Cleans up old data                                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  /data/     │
                   │   weather/  │
                   └─────────────┘
```

> **Note**: This system uses THREDDS (Thematic Real-time Environmental Distributed Data Services), the industry-standard server for atmospheric and oceanographic data used by NOAA, UCAR, and major weather services worldwide. See [THREDDS.md](THREDDS.md) for detailed documentation.

## Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **4GB RAM minimum** (recommended: 8GB)
- **10GB free disk space**
- **Internet connection** (for downloading weather data)

## Quick Start

### 1. Clone or Download

```bash
# If using git
git clone <repository-url>
cd weather-viz

# Or download and extract the archive
```

### 2. Create Data Directory

```bash
mkdir -p data/weather
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start three services:
- **thredds** (port 8080): THREDDS Data Server with WMS, OPeNDAP, and other services
- **data-fetcher**: Weather data downloader
- **nginx** (port 80): Frontend web server

### 4. Wait for Initial Data Download

The first data fetch takes 15-30 minutes depending on your connection. Monitor progress:

```bash
docker-compose logs -f data-fetcher
```

### 5. Access Application

Open your browser and navigate to:
```
http://localhost
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory to customize settings:

```env
# Data fetcher settings
DATA_DIR=/data/weather
FETCH_INTERVAL=21600  # 6 hours in seconds
NOAA_BASE_URL=https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl

# ncWMS2 settings
JAVA_OPTS=-Xmx2g

# Nginx settings
NGINX_PORT=80
NCWMS_PORT=8080
```

### Weather Parameters

Available parameters (configured in `backend/config/catalog.xml`):
- Temperature at 2m (°C)
- Temperature at 850mb (°C)
- Wind Speed at 10m (m/s)
- Wind Speed at 50m (m/s)
- Precipitation Rate (mm/hr)
- Mean Sea Level Pressure (hPa)
- Relative Humidity (%)

## Usage Guide

### Map Controls

- **Pan**: Click and drag the map
- **Zoom**: Scroll wheel or use +/- buttons
- **Reset**: Double-click to reset view

### Animation Controls

- **Play/Pause**: Click the play button or press `Space`
- **Stop**: Reset animation to first frame
- **Speed**: Select 0.5x, 1x, 2x, or 4x playback speed
- **Timeline**: Drag slider or use arrow keys to navigate frames

### Keyboard Shortcuts

- `Space`: Toggle play/pause
- `←`: Previous frame
- `→`: Next frame
- `Esc`: Stop animation

### Parameter Selection

Use the dropdown menu to switch between weather parameters. The legend and color scale will update automatically.

### Layer Controls

- **Toggle Visibility**: Checkbox to show/hide weather layer
- **Opacity**: Slider to adjust layer transparency (0-100%)

## Project Structure

```
weather-viz/
├── docker-compose.yml          # Docker services configuration
├── README.md                   # This file
├── .env                        # Environment variables (create this)
│
├── backend/
│   ├── data-fetcher/
│   │   ├── Dockerfile          # Data fetcher container
│   │   ├── requirements.txt    # Python dependencies
│   │   ├── fetch_weather.py    # Main data fetcher script
│   │   └── run.sh             # Startup script
│   └── config/
│       └── ncwms-config.xml   # ncWMS2 configuration
│
├── frontend/
│   ├── index.html             # Main HTML file
│   ├── css/
│   │   └── style.css          # Application styles
│   └── js/
│       ├── app.js             # Main application
│       ├── map.js             # Map management
│       ├── animation.js       # Animation system
│       └── controls.js        # UI controls
│
├── nginx/
│   └── nginx.conf             # Nginx configuration
│
└── data/
    └── weather/               # Weather data storage (created on first run)
```

## Troubleshooting

### Service Won't Start

**Problem**: Docker containers fail to start

**Solutions**:
```bash
# Check if ports are already in use
sudo lsof -i :80    # Frontend
sudo lsof -i :8080  # ncWMS2

# Check Docker logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### No Weather Data Available

**Problem**: Application shows "No weather data available"

**Solutions**:
1. Check if data fetcher is running:
   ```bash
   docker-compose ps
   ```

2. Monitor data fetcher logs:
   ```bash
   docker-compose logs -f data-fetcher
   ```

3. Manually trigger data fetch:
   ```bash
   docker-compose exec data-fetcher python fetch_weather.py
   ```

4. Check if data directory exists:
   ```bash
   ls -la data/weather/
   ```

### Map Tiles Not Loading

**Problem**: Weather overlay doesn't appear

**Solutions**:
1. Check THREDDS service:
   ```bash
   curl http://localhost:8080/thredds/catalog.html
   ```

2. Verify NetCDF files exist:
   ```bash
   ls data/weather/*.nc
   ```

3. Check browser console for errors (F12)

4. Ensure CORS is properly configured in nginx

5. Verify catalog configuration:
   ```bash
   docker-compose exec thredds cat /usr/local/tomcat/content/thredds/catalog.xml
   ```

### Slow Performance

**Problem**: Animation stutters or is slow

**Solutions**:
1. Increase Docker memory allocation (8GB recommended)
2. Reduce animation speed
3. Close other browser tabs
4. Check system resources:
   ```bash
   docker stats
   ```

### Data Download Fails

**Problem**: NOAA data download errors

**Solutions**:
1. Check internet connectivity
2. Verify NOAA NOMADS server is accessible:
   ```bash
   curl -I https://nomads.ncep.noaa.gov/
   ```
3. Check data fetcher logs for specific errors
4. Try again later (server may be temporarily down)

## Performance Optimization

### System Requirements by Usage

- **Light**: 2GB RAM, 5GB disk (one dataset, low resolution)
- **Standard**: 4GB RAM, 10GB disk (full dataset, standard resolution)
- **Heavy**: 8GB+ RAM, 20GB+ disk (multiple datasets, high resolution)

### Optimization Tips

1. **Reduce Data Retention**:
   Edit `fetch_weather.py` to keep fewer hours:
   ```python
   cleanup_old_data(max_age_hours=24)  # Instead of 48
   ```

2. **Download Fewer Forecast Hours**:
   Edit `fetch_weather.py`:
   ```python
   forecast_hours = list(range(0, 25, 6))  # 0-24hrs in 6hr increments
   ```

3. **Pre-generate Tile Cache**:
   Enable GeoWebCache in ncWMS2 configuration

4. **Reduce Parameter Count**:
   Comment out unused parameters in `ncwms-config.xml`

## Development

### Running in Development Mode

```bash
# Frontend development (with hot reload)
cd frontend
python -m http.server 8000

# Backend development
docker-compose up thredds data-fetcher
```

### Modifying Weather Parameters

1. Edit `backend/config/catalog.xml` to add/modify dataset scans
2. Edit `frontend/js/map.js` WEATHER_LAYERS object
3. Edit `frontend/index.html` select options
4. Restart services:
   ```bash
   docker-compose restart thredds
   ```

### Custom Color Scales

THREDDS supports various color palettes:
- rainbow
- blues, greens, reds
- rdylgn (Red-Yellow-Green)
- greyscale
- And many more

Edit color palette in `frontend/js/map.js` WEATHER_LAYERS configuration.

## API Documentation

For complete THREDDS API documentation, see [THREDDS.md](THREDDS.md).

### Quick Reference - WMS Endpoints

#### GetCapabilities
```
GET http://localhost:8080/thredds/wms?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0
```

#### GetMap
```
GET http://localhost:8080/thredds/wms?
  SERVICE=WMS
  &REQUEST=GetMap
  &VERSION=1.3.0
  &LAYERS=weather/temp_2m
  &STYLES=rainbow
  &CRS=EPSG:3857
  &BBOX=minx,miny,maxx,maxy
  &WIDTH=800
  &HEIGHT=600
  &FORMAT=image/png
  &TRANSPARENT=true
  &COLORSCALERANGE=-40,50
  &TIME=2025-10-27T12:00:00Z
```

#### GetFeatureInfo
```
GET http://localhost:8080/thredds/wms?
  SERVICE=WMS
  &REQUEST=GetFeatureInfo
  &VERSION=1.3.0
  &LAYERS=weather/temp_2m
  &QUERY_LAYERS=weather/temp_2m
  &INFO_FORMAT=application/json
  &I=400
  &J=300
  &TIME=2025-10-27T12:00:00Z
```

### OPeNDAP Access

```
# Python example
import xarray as xr
url = "http://localhost:8080/thredds/dodsC/weather/temp_2m/temp_2m_2024010100.nc"
ds = xr.open_dataset(url)
```

For more examples and detailed documentation, see [THREDDS.md](THREDDS.md).

## Maintenance

### Update Weather Data

Data updates automatically every 6 hours. To force update:
```bash
docker-compose exec data-fetcher python fetch_weather.py
```

### Clean Old Data

```bash
# Manual cleanup
docker-compose exec data-fetcher python -c "from fetch_weather import cleanup_old_data; cleanup_old_data(24)"
```

### Backup Data

```bash
# Backup current data
tar -czf weather-data-backup-$(date +%Y%m%d).tar.gz data/weather/

# Restore from backup
tar -xzf weather-data-backup-YYYYMMDD.tar.gz
```

### Update System

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Contributing

Contributions are welcome! Areas for improvement:
- Additional weather parameters
- Historical data playback
- Weather alerts integration
- Mobile app version
- Export to GIF/video
- Multi-language support

## License

MIT License - see LICENSE file for details

## Credits

- **Weather Data**: NOAA GFS (Global Forecast System)
- **Map Library**: OpenLayers
- **Data Server**: THREDDS (Unidata)
- **Base Map**: OpenStreetMap

## Support

For issues and questions:
1. Check the Troubleshooting section above
2. Review Docker logs: `docker-compose logs`
3. Check browser console (F12) for JavaScript errors
4. Ensure all prerequisites are installed

## Changelog

### Version 1.0.0 (2025-10-27)
- Initial release
- Support for 7 weather parameters
- Animation controls with variable speed
- Dark mode support
- Responsive design
- Keyboard shortcuts
- Real-time value display on hover
