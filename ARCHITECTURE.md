# New Architecture: Python Weather Processor + Golang WMS Server

## Overview
This document describes the new architecture replacing THREDDS with a custom Golang WMS tile server.

## Architecture Diagram

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
│          Golang WMS Tile Server (Port 8080)              │
│  • WMS GetCapabilities                                  │
│  • WMS GetMap (tile generation)                         │
│  • WMS GetFeatureInfo                                   │
│  • Reads processed tile data from shared volume         │
│  • Fast tile serving with caching                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         Python Weather Processor (Port 8081)             │
│  • Downloads NOAA GFS GRIB2 data                        │
│  • Converts to NetCDF format                            │
│  • Pre-processes tiles for each parameter               │
│  • Generates metadata for WMS server                    │
│  • Runs every 6 hours                                   │
│  • Provides HTTP API for metadata queries               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  /data/     │
                   │   weather/  │
                   │   tiles/    │
                   │   metadata/ │
                   └─────────────┘
```

## Components

### 1. Python Weather Processor
**Purpose**: Download, process, and prepare weather data for the WMS server

**Responsibilities**:
- Download NOAA GFS GRIB2 data
- Convert to NetCDF format
- Extract and process weather parameters
- Generate tile metadata (bounds, time steps, color scales)
- Store processed data in efficient format
- Provide HTTP API for metadata queries
- Clean up old data

**Technology**: Python 3.11+ with xarray, cfgrib, numpy, Flask

**Output Format**:
```
/data/weather/
  ├── netcdf/              # Raw NetCDF files
  │   ├── temp_2m_2024010100.nc
  │   └── ...
  ├── metadata/            # JSON metadata for WMS
  │   ├── temp_2m.json
  │   └── ...
  └── cache/               # Optional pre-rendered tiles
      └── ...
```

### 2. Golang WMS Tile Server
**Purpose**: Serve weather data as WMS tiles with high performance

**Responsibilities**:
- Implement WMS 1.3.0 protocol
- GetCapabilities: Return available layers and time steps
- GetMap: Generate PNG tiles on-demand
- GetFeatureInfo: Return values at specific coordinates
- Read NetCDF files efficiently
- Apply color scales and styling
- Cache frequently requested tiles
- Handle concurrent requests

**Technology**: Go 1.21+ with:
- `github.com/fhs/go-netcdf/netcdf` - NetCDF reading
- `github.com/fogleman/gg` - Image generation
- `github.com/gorilla/mux` - HTTP routing
- Built-in concurrency with goroutines

**Endpoints**:
```
GET /wms?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0
GET /wms?SERVICE=WMS&REQUEST=GetMap&...
GET /wms?SERVICE=WMS&REQUEST=GetFeatureInfo&...
GET /health
GET /metrics
```

### 3. Frontend (Unchanged)
The frontend remains the same, only the WMS endpoint URL changes from THREDDS to the new Golang server.

## Data Flow

1. **Data Acquisition** (Python)
   - Download GRIB2 from NOAA every 6 hours
   - Convert to NetCDF with proper CF conventions
   - Extract variables and metadata

2. **Data Processing** (Python)
   - Calculate derived parameters (wind speed)
   - Generate metadata JSON files
   - Optionally pre-render common tiles

3. **Tile Serving** (Golang)
   - Read NetCDF files on-demand
   - Apply color scales and projections
   - Generate PNG tiles
   - Cache results in memory
   - Serve via WMS protocol

4. **Visualization** (Frontend)
   - Request tiles via WMS GetMap
   - Display on OpenLayers map
   - Query values via GetFeatureInfo

## Advantages Over THREDDS

1. **Simplicity**: No Java/Tomcat overhead, simpler deployment
2. **Performance**: Go's concurrency and efficiency
3. **Customization**: Full control over tile generation and caching
4. **Resource Usage**: Lower memory footprint
5. **Startup Time**: Faster startup (seconds vs minutes)
6. **Maintenance**: Easier to debug and modify
7. **Size**: Smaller Docker images

## Implementation Plan

### Phase 1: Python Weather Processor
- [x] Design architecture
- [ ] Enhance fetch_weather.py with metadata generation
- [ ] Add HTTP API for metadata queries
- [ ] Create metadata JSON schema
- [ ] Test data processing pipeline

### Phase 2: Golang WMS Server
- [ ] Set up Go project structure
- [ ] Implement WMS GetCapabilities
- [ ] Implement WMS GetMap with NetCDF reading
- [ ] Implement WMS GetFeatureInfo
- [ ] Add color scale rendering
- [ ] Add tile caching
- [ ] Add health checks and metrics

### Phase 3: Integration
- [ ] Create Dockerfiles for both services
- [ ] Update docker-compose.yml
- [ ] Update frontend WMS endpoint
- [ ] Test complete system
- [ ] Performance testing and optimization

### Phase 4: Documentation
- [ ] Update README.md
- [ ] Create API documentation
- [ ] Add deployment guide
- [ ] Performance tuning guide

## File Structure

```
weather/
├── backend/
│   ├── processor/              # Python weather processor
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── processor.py        # Main processor
│   │   ├── metadata.py         # Metadata generation
│   │   ├── api.py              # HTTP API
│   │   └── config.py           # Configuration
│   │
│   └── wms-server/             # Golang WMS server
│       ├── Dockerfile
│       ├── go.mod
│       ├── go.sum
│       ├── main.go
│       ├── wms/                # WMS protocol implementation
│       │   ├── capabilities.go
│       │   ├── getmap.go
│       │   └── featureinfo.go
│       ├── netcdf/             # NetCDF reading
│       │   └── reader.go
│       ├── render/             # Tile rendering
│       │   ├── colorscale.go
│       │   └── tile.go
│       └── cache/              # Caching layer
│           └── cache.go
│
├── frontend/                   # Unchanged
├── nginx/                      # Minor config updates
└── docker-compose.yml          # Updated services
```

## Configuration

### Python Processor Environment Variables
```env
DATA_DIR=/data/weather
FETCH_INTERVAL=21600
NOAA_BASE_URL=https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl
API_PORT=8081
METADATA_DIR=/data/weather/metadata
```

### Golang WMS Server Environment Variables
```env
DATA_DIR=/data/weather
PORT=8080
CACHE_SIZE=1000
MAX_WORKERS=10
LOG_LEVEL=info
```

## Performance Targets

- **Tile Generation**: < 100ms per tile
- **Memory Usage**: < 1GB for WMS server
- **Startup Time**: < 10 seconds
- **Concurrent Requests**: 100+ simultaneous
- **Cache Hit Rate**: > 80% for common tiles

## Next Steps

1. Implement Python metadata generation
2. Build Golang WMS server
3. Test integration
4. Deploy and benchmark
