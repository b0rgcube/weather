#!/usr/bin/env python3
"""
Weather Data Fetcher for NOAA GFS
Downloads GRIB2 data and converts to NetCDF for ncWMS2
"""

import os
import sys
import logging
import requests
import xarray as xr
import cfgrib
from datetime import datetime, timedelta
from pathlib import Path
import time
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = os.getenv('DATA_DIR', '/data/weather')
NOAA_BASE_URL = "http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
MAX_RETRIES = 1
RETRY_DELAY = 10  # seconds

# Weather parameters to download
WEATHER_PARAMS = {
    'TMP:2 m above ground': 'temp_2m',
    'TMP:850 mb': 'temp_850mb',
    'UGRD:10 m above ground': 'u_wind_10m',
    'VGRD:10 m above ground': 'v_wind_10m',
    'UGRD:50 m above ground': 'u_wind_50m',
    'VGRD:50 m above ground': 'v_wind_50m',
    'PRATE:surface': 'precip_rate',
    'PRMSL:mean sea level': 'mslp',
    'RH:2 m above ground': 'rh_2m'
}

def get_latest_run():
    """Get the latest available GFS run time"""
    now = datetime.utcnow()
    # GFS runs at 00, 06, 12, 18 UTC
    run_hour = (now.hour // 6) * 6
    # Use previous run to ensure data is available
    run_time = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
    if now.hour - run_hour < 4:  # Data might not be ready yet
        run_time -= timedelta(hours=6)
    return run_time

def build_download_url(run_time, forecast_hour, param):
    """Build NOAA NOMADS download URL for specific parameter"""
    date_str = run_time.strftime('%Y%m%d')
    hour_str = run_time.strftime('%H')
    
    # Extract variable name from parameter
    var_name = param.split(':')[0]
    level = ':'.join(param.split(':')[1:])
    
    url = f"{NOAA_BASE_URL}?"
    url += f"file=gfs.t{hour_str}z.pgrb2.0p25.f{forecast_hour:03d}"
    url += f"&lev_{level.replace(' ', '_').replace(':', '%3A')}=on"
    url += f"&var_{var_name}=on"
    url += "&subregion=&leftlon=0&rightlon=360&toplat=90&bottomlat=-90"
    url += f"&dir=%2Fgfs.{date_str}%2F{hour_str}%2Fatmos"
    
    return url

def download_grib_data(run_time, forecast_hour, param, output_file):
    """Download GRIB2 data with retry logic"""
    url = build_download_url(run_time, forecast_hour, param)
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Downloading {param} for forecast hour {forecast_hour} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, timeout=300, verify=False)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded to {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to download after {MAX_RETRIES} attempts")
                return False
    
    return False

def convert_to_netcdf(grib_files, output_file, param_name):
    """Convert GRIB2 files to NetCDF with flattened time dimension for GeoServer compatibility"""
    try:
        logger.info(f"Converting GRIB files to NetCDF: {output_file}")
        
        # Read all GRIB files
        datasets = []
        for grib_file in sorted(grib_files):
            try:
                ds = xr.open_dataset(grib_file, engine='cfgrib')
                
                # Flatten time dimensions: use valid_time if available, otherwise compute it
                if 'valid_time' in ds.coords:
                    # Set 'time' coordinate values from 'valid_time' to avoid rename conflicts
                    ds = ds.assign_coords(time=ds['valid_time'])
                    # Drop helper coords
                    ds = ds.drop_vars('valid_time', errors='ignore')
                    if 'step' in ds.coords:
                        ds = ds.drop_vars('step', errors='ignore')
                elif 'time' in ds.coords and 'step' in ds.coords:
                    # Compute valid_time from time + step and assign to 'time', then drop step
                    ds = ds.assign_coords(time=ds.time + ds.step)
                    ds = ds.drop_vars('step', errors='ignore')
                
                # Expand time dimension if it's scalar
                if 'time' in ds.dims and ds.dims['time'] == 0:
                    ds = ds.expand_dims('time')
                
                datasets.append(ds)
            except Exception as e:
                logger.warning(f"Could not read {grib_file}: {e}")
                continue
        
        if not datasets:
            logger.error("No valid GRIB files to convert")
            return False
        
        # Concatenate along time dimension
        combined = xr.concat(datasets, dim='time')
        
        # Remove problematic coordinates that GeoServer doesn't support
        coords_to_drop = []
        for coord in combined.coords:
            # Keep only essential coordinates
            if coord not in ['time', 'latitude', 'longitude']:
                coords_to_drop.append(coord)
        
        if coords_to_drop:
            logger.info(f"Dropping coordinates: {coords_to_drop}")
            combined = combined.drop_vars(coords_to_drop, errors='ignore')
        
        # Add metadata
        combined.attrs['title'] = f'GFS Weather Data - {param_name}'
        combined.attrs['institution'] = 'NOAA/NCEP'
        combined.attrs['source'] = 'GFS 0.25 degree'
        combined.attrs['Conventions'] = 'CF-1.6'
        
        # Save as NetCDF with CF-compliant time encoding
        encoding = {}
        for var in combined.data_vars:
            encoding[var] = {'zlib': True, 'complevel': 5}
        
        # Ensure time has proper encoding
        if 'time' in combined.coords:
            encoding['time'] = {'units': 'seconds since 1970-01-01', 'calendar': 'gregorian'}
        
        combined.to_netcdf(output_file, encoding=encoding)
        
        logger.info(f"Successfully created NetCDF: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting to NetCDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def calculate_wind_speed(u_files, v_files, output_file):
    """Calculate wind speed from U and V components"""
    try:
        logger.info(f"Calculating wind speed: {output_file}")
        
        u_datasets = [xr.open_dataset(f, engine='cfgrib') for f in sorted(u_files)]
        v_datasets = [xr.open_dataset(f, engine='cfgrib') for f in sorted(v_files)]
        
        u_combined = xr.concat(u_datasets, dim='time')
        v_combined = xr.concat(v_datasets, dim='time')
        
        # Calculate wind speed: sqrt(u^2 + v^2)
        wind_speed = xr.Dataset({
            'wind_speed': (u_combined.u ** 2 + v_combined.v ** 2) ** 0.5
        })
        
        wind_speed.attrs['title'] = 'Wind Speed'
        wind_speed.attrs['units'] = 'm/s'
        
        encoding = {'wind_speed': {'zlib': True, 'complevel': 5}}
        wind_speed.to_netcdf(output_file, encoding=encoding)
        
        logger.info(f"Successfully created wind speed NetCDF: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error calculating wind speed: {e}")
        return False

def cleanup_old_data(max_age_hours=48):
    """Remove data older than specified hours"""
    try:
        logger.info(f"Cleaning up data older than {max_age_hours} hours")
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for file_path in Path(DATA_DIR).glob('*.nc'):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                logger.info(f"Removing old file: {file_path}")
                file_path.unlink()
        
        # Also clean up GRIB files
        for file_path in Path(DATA_DIR).glob('*.grb2'):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                logger.info(f"Removing old GRIB file: {file_path}")
                file_path.unlink()
                
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def fetch_weather_data():
    """Main function to fetch and process weather data"""
    logger.info("Starting weather data fetch")
    
    # Ensure data directory exists
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    # Get latest run time
    run_time = get_latest_run()
    logger.info(f"Fetching data for run: {run_time.strftime('%Y%m%d %H:00 UTC')}")
    
    # Download forecast hours (0-48 in 3-hour increments)
    forecast_hours = list(range(0, 49, 3))
    
    # Download each parameter
    for param, param_name in WEATHER_PARAMS.items():
        logger.info(f"Processing parameter: {param_name}")
        grib_files = []
        
        for fh in forecast_hours:
            grib_file = Path(DATA_DIR) / f"gfs_{param_name}_f{fh:03d}.grb2"
            if download_grib_data(run_time, fh, param, grib_file):
                grib_files.append(str(grib_file))
        
        if grib_files:
            nc_file = Path(DATA_DIR) / f"{param_name}_{run_time.strftime('%Y%m%d%H')}.nc"
            convert_to_netcdf(grib_files, str(nc_file), param_name)
            
            # Clean up GRIB files after conversion
            for grib_file in grib_files:
                try:
                    Path(grib_file).unlink()
                except:
                    pass
    
    # Calculate wind speeds
    logger.info("Calculating wind speeds")
    
    # 10m wind
    u10_files = glob.glob(os.path.join(DATA_DIR, 'gfs_u_wind_10m_*.grb2'))
    v10_files = glob.glob(os.path.join(DATA_DIR, 'gfs_v_wind_10m_*.grb2'))
    if u10_files and v10_files:
        ws10_file = Path(DATA_DIR) / f"wind_speed_10m_{run_time.strftime('%Y%m%d%H')}.nc"
        calculate_wind_speed(u10_files, v10_files, str(ws10_file))
    
    # 50m wind
    u50_files = glob.glob(os.path.join(DATA_DIR, 'gfs_u_wind_50m_*.grb2'))
    v50_files = glob.glob(os.path.join(DATA_DIR, 'gfs_v_wind_50m_*.grb2'))
    if u50_files and v50_files:
        ws50_file = Path(DATA_DIR) / f"wind_speed_50m_{run_time.strftime('%Y%m%d%H')}.nc"
        calculate_wind_speed(u50_files, v50_files, str(ws50_file))
    
    # Cleanup old data
    cleanup_old_data()
    
    logger.info("Weather data fetch completed")

if __name__ == '__main__':
    try:
        fetch_weather_data()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
