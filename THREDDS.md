# THREDDS Data Server Configuration

This document explains the THREDDS Data Server setup for serving weather data.

## Overview

THREDDS (Thematic Real-time Environmental Distributed Data Services) is an industry-standard server for atmospheric and oceanographic data. It's used by NOAA, UCAR, and major weather services worldwide for serving NetCDF datasets.

## Architecture

```
┌─────────────────────┐
│  THREDDS Server     │  Port 8080
│  (Tomcat-based)     │
└──────────┬──────────┘
           │
           ├─ WMS Service     (/thredds/wms)
           ├─ OPeNDAP        (/thredds/dodsC)
           ├─ NetCDF Subset  (/thredds/ncss)
           ├─ WCS Service    (/thredds/wcs)
           └─ HTTP Server    (/thredds/fileServer)
           
           ↓
    
┌──────────────────────┐
│   NetCDF Files       │
│  /data/weather/      │
└──────────────────────┘
```

## Accessing THREDDS

### Web Interface

Access the THREDDS catalog browser:
```
http://localhost:8080/thredds/catalog.html
```

Browse datasets and view metadata, documentation, and available services.

### WMS Endpoints

The Web Map Service (WMS) endpoints used by the frontend application:

**Base URL:**
```
http://localhost:8080/thredds/wms
```

**Available Datasets:**
- `weather/temp_2m` - Temperature at 2m
- `weather/temp_850mb` - Temperature at 850mb
- `weather/wind_speed_10m` - Wind speed at 10m
- `weather/wind_speed_50m` - Wind speed at 50m
- `weather/precip_rate` - Precipitation rate
- `weather/mslp` - Mean sea level pressure
- `weather/rh_2m` - Relative humidity at 2m

**Example WMS GetMap Request:**
```
http://localhost:8080/thredds/wms?
  SERVICE=WMS&
  VERSION=1.3.0&
  REQUEST=GetMap&
  LAYERS=weather/temp_2m&
  STYLES=rainbow&
  CRS=EPSG:4326&
  BBOX=-90,-180,90,180&
  WIDTH=800&
  HEIGHT=400&
  FORMAT=image/png&
  TRANSPARENT=true&
  COLORSCALERANGE=-40,50&
  TIME=2024-01-01T00:00:00Z
```

### OPeNDAP Access

Access NetCDF data programmatically using OPeNDAP:

**Base URL:**
```
http://localhost:8080/thredds/dodsC/weather/
```

**Python Example:**
```python
import xarray as xr

# Open remote NetCDF file via OPeNDAP
url = "http://localhost:8080/thredds/dodsC/weather/temp_2m/temp_2m_2024010100.nc"
ds = xr.open_dataset(url)

# Access data
temperature = ds['t2m']
print(temperature)
```

**Matlab Example:**
```matlab
% Access NetCDF via OPeNDAP
url = 'http://localhost:8080/thredds/dodsC/weather/temp_2m/temp_2m_2024010100.nc';
ncdisp(url);
temp = ncread(url, 't2m');
```

### NetCDF Subset Service (NCSS)

Extract subsets of data by time, space, or variable:

**Base URL:**
```
http://localhost:8080/thredds/ncss/weather/
```

**Example Request:**
```
http://localhost:8080/thredds/ncss/weather/temp_2m/temp_2m_2024010100.nc?
  var=t2m&
  north=60&south=40&west=-10&east=10&
  time_start=2024-01-01T00:00:00Z&
  time_end=2024-01-01T12:00:00Z&
  accept=netcdf
```

### Web Coverage Service (WCS)

Access gridded data using OGC WCS standard:

**Base URL:**
```
http://localhost:8080/thredds/wcs
```

## Catalog Configuration

The catalog is defined in `backend/config/catalog.xml`:

```xml
<catalog name="Weather Data Catalog">
  <service name="all" serviceType="Compound" base="">
    <service name="wms" serviceType="WMS" base="/thredds/wms/"/>
    <service name="odap" serviceType="OPENDAP" base="/thredds/dodsC/"/>
    <!-- ... other services -->
  </service>
  
  <dataset name="GFS Weather Data">
    <datasetScan name="Temperature at 2m" 
                 path="weather/temp_2m"
                 location="/usr/local/tomcat/content/thredds/public/weather/">
      <filter>
        <include wildcard="temp_2m_*.nc"/>
      </filter>
    </datasetScan>
    <!-- ... other datasets -->
  </dataset>
</catalog>
```

### Key Configuration Elements

1. **Services** - Defines available protocols (WMS, OPeNDAP, NCSS, etc.)
2. **DatasetScan** - Automatically discovers NetCDF files matching patterns
3. **Metadata** - CF-1.6 conventions, geospatial coverage, documentation
4. **Filters** - Include/exclude files based on wildcards

## Docker Configuration

THREDDS runs in a Docker container configured in `docker-compose.yml`:

```yaml
thredds:
  image: unidata/thredds-docker:5.5
  ports:
    - "8080:8080"
  volumes:
    - ./data/weather:/usr/local/tomcat/content/thredds/public/weather:ro
    - ./backend/config/catalog.xml:/usr/local/tomcat/content/thredds/catalog.xml:ro
  environment:
    - THREDDS_XMX_SIZE=4G
    - THREDDS_XMS_SIZE=1G
```

### Volume Mounts

- **Weather Data**: NetCDF files are mounted read-only from `./data/weather`
- **Catalog**: Custom catalog configuration is mounted at startup
- **Config Volume**: Persistent storage for THREDDS configuration

### Memory Configuration

- Initial heap: 1GB (`THREDDS_XMS_SIZE`)
- Maximum heap: 4GB (`THREDDS_XMX_SIZE`)

Adjust based on your dataset size and server resources.

## Monitoring THREDDS

### Health Check

THREDDS includes a health check in docker-compose:
```bash
curl -f http://localhost:8080/thredds/catalog.html
```

### Logs

View THREDDS logs:
```bash
docker logs weather-thredds
```

Follow logs in real-time:
```bash
docker logs -f weather-thredds
```

### Admin Interface

Access THREDDS admin interface (if enabled):
```
http://localhost:8080/thredds/admin/debug
```

## WMS Parameters Reference

### Standard WMS Parameters

- `SERVICE=WMS` - Service type
- `VERSION=1.3.0` - WMS version
- `REQUEST=GetMap|GetCapabilities|GetFeatureInfo` - Request type
- `LAYERS=weather/temp_2m` - Layer name
- `CRS=EPSG:4326` - Coordinate reference system
- `BBOX=minx,miny,maxx,maxy` - Bounding box
- `WIDTH=800` - Image width in pixels
- `HEIGHT=400` - Image height in pixels
- `FORMAT=image/png` - Output format

### THREDDS-Specific Parameters

- `STYLES=rainbow` - Color palette (rainbow, blues, greyscale, etc.)
- `COLORSCALERANGE=min,max` - Data value range for colors
- `NUMCOLORBANDS=250` - Number of color bands
- `ABOVEMAXCOLOR=extend` - Color for values above max
- `BELOWMINCOLOR=extend` - Color for values below min
- `TIME=2024-01-01T00:00:00Z` - Time dimension value
- `ELEVATION=0` - Elevation/vertical level (if applicable)

## Color Palettes

THREDDS supports various color palettes:

- `rainbow` - Rainbow spectrum
- `blues` - Blue shades (good for humidity, precipitation)
- `reds` - Red shades
- `greyscale` - Grayscale
- `rdylgn` - Red-Yellow-Green diverging (good for pressure)
- `rdylbu` - Red-Yellow-Blue diverging
- Custom palettes can be defined

## Troubleshooting

### THREDDS Not Starting

1. Check container logs:
   ```bash
   docker logs weather-thredds
   ```

2. Verify catalog XML is valid:
   ```bash
   xmllint --noout backend/config/catalog.xml
   ```

3. Ensure ports are not in use:
   ```bash
   lsof -i :8080
   ```

### WMS Not Displaying Data

1. Verify NetCDF files exist:
   ```bash
   ls -la data/weather/
   ```

2. Check GetCapabilities response:
   ```bash
   curl "http://localhost:8080/thredds/wms?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0"
   ```

3. Test direct file access via OPeNDAP:
   ```bash
   curl "http://localhost:8080/thredds/dodsC/weather/temp_2m/temp_2m_2024010100.nc.das"
   ```

### Performance Issues

1. Increase memory allocation in docker-compose.yml
2. Enable caching in THREDDS configuration
3. Use aggregation for multiple files
4. Consider data chunking in NetCDF files

## Best Practices

1. **CF Conventions**: Ensure NetCDF files follow CF-1.6 conventions
2. **Metadata**: Include comprehensive metadata in NetCDF files
3. **File Naming**: Use consistent, sortable naming patterns
4. **Chunking**: Optimize NetCDF chunking for your access patterns
5. **Compression**: Use compression (e.g., zlib) to reduce file sizes
6. **Aggregation**: Use THREDDS aggregation for time series
7. **Security**: Restrict access to admin interfaces in production
8. **Monitoring**: Set up monitoring and alerting for THREDDS

## Additional Resources

- [THREDDS Documentation](https://docs.unidata.ucar.edu/tds/current/userguide/)
- [CF Conventions](http://cfconventions.org/)
- [WMS Specification](https://www.ogc.org/standards/wms)
- [OPeNDAP Protocol](https://www.opendap.org/)
- [Unidata THREDDS Docker](https://github.com/Unidata/thredds-docker)
