#!/usr/bin/env python3
"""
Weather Data Processor
Downloads NOAA GFS data, converts to NetCDF, and generates metadata
Combines functionality from fetch_weather.py with metadata generation
"""

import os
import sys
import logging
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

# Import existing fetch functionality
sys.path.insert(0, str(Path(__file__).parent.parent / 'data-fetcher'))
from fetch_weather import (
    get_latest_run,
    download_grib_data,
    convert_to_netcdf,
    calculate_wind_speed,
    cleanup_old_data,
    WEATHER_PARAMS,
    DATA_DIR as FETCH_DATA_DIR
)

# Import metadata generation
from metadata import generate_layer_metadata
from api import run_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path(os.getenv('DATA_DIR', '/data/weather'))
METADATA_DIR = DATA_DIR / 'metadata'
FETCH_INTERVAL = int(os.getenv('FETCH_INTERVAL', 21600))  # 6 hours
API_PORT = int(os.getenv('API_PORT', 8081))
RUN_API = os.getenv('RUN_API', 'true').lower() == 'true'


def process_weather_data():
    """
    Main processing function:
    1. Download NOAA GFS data
    2. Convert to NetCDF
    3. Generate metadata
    """
    logger.info("=" * 80)
    logger.info("Starting weather data processing cycle")
    logger.info("=" * 80)
    
    try:
        # Ensure directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Get latest run time
        run_time = get_latest_run()
        logger.info(f"Processing data for run: {run_time.strftime('%Y%m%d %H:00 UTC')}")
        
        # Download forecast hours (0-48 in 3-hour increments)
        forecast_hours = list(range(0, 49, 3))
        
        # Track successful downloads
        successful_params = []
        
        # Download and convert each parameter
        for param, param_name in WEATHER_PARAMS.items():
            logger.info(f"Processing parameter: {param_name}")
            grib_files = []
            
            for fh in forecast_hours:
                grib_file = DATA_DIR / f"gfs_{param_name}_f{fh:03d}.grb2"
                if download_grib_data(run_time, fh, param, grib_file):
                    grib_files.append(str(grib_file))
                else:
                    logger.warning(f"Failed to download {param_name} for hour {fh}")
            
            if grib_files:
                nc_file = DATA_DIR / f"{param_name}_{run_time.strftime('%Y%m%d%H')}.nc"
                if convert_to_netcdf(grib_files, str(nc_file), param_name):
                    successful_params.append(param_name)
                    logger.info(f"Successfully processed {param_name}")
                
                # Clean up GRIB files after conversion
                for grib_file in grib_files:
                    try:
                        Path(grib_file).unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete {grib_file}: {e}")
            else:
                logger.error(f"No data downloaded for {param_name}")
        
        # Calculate wind speeds if we have the components
        logger.info("Calculating wind speeds")
        
        # Check for wind component files
        u10_nc = DATA_DIR / f"u_wind_10m_{run_time.strftime('%Y%m%d%H')}.nc"
        v10_nc = DATA_DIR / f"v_wind_10m_{run_time.strftime('%Y%m%d%H')}.nc"
        
        if u10_nc.exists() and v10_nc.exists():
            ws10_file = DATA_DIR / f"wind_speed_10m_{run_time.strftime('%Y%m%d%H')}.nc"
            try:
                # Read and calculate wind speed
                import xarray as xr
                u_ds = xr.open_dataset(u10_nc)
                v_ds = xr.open_dataset(v10_nc)
                
                # Get variable names
                u_var = list(u_ds.data_vars)[0]
                v_var = list(v_ds.data_vars)[0]
                
                # Calculate wind speed
                wind_speed = (u_ds[u_var] ** 2 + v_ds[v_var] ** 2) ** 0.5
                
                # Create new dataset
                ws_ds = xr.Dataset({
                    'wind_speed': wind_speed
                })
                ws_ds.attrs['title'] = 'Wind Speed 10m'
                ws_ds.attrs['units'] = 'm/s'
                
                # Save
                encoding = {'wind_speed': {'zlib': True, 'complevel': 5}}
                ws_ds.to_netcdf(ws10_file, encoding=encoding)
                
                successful_params.append('wind_speed_10m')
                logger.info("Successfully calculated wind_speed_10m")
                
                u_ds.close()
                v_ds.close()
                ws_ds.close()
                
            except Exception as e:
                logger.error(f"Error calculating wind_speed_10m: {e}")
        
        # Same for 50m wind
        u50_nc = DATA_DIR / f"u_wind_50m_{run_time.strftime('%Y%m%d%H')}.nc"
        v50_nc = DATA_DIR / f"v_wind_50m_{run_time.strftime('%Y%m%d%H')}.nc"
        
        if u50_nc.exists() and v50_nc.exists():
            ws50_file = DATA_DIR / f"wind_speed_50m_{run_time.strftime('%Y%m%d%H')}.nc"
            try:
                import xarray as xr
                u_ds = xr.open_dataset(u50_nc)
                v_ds = xr.open_dataset(v50_nc)
                
                u_var = list(u_ds.data_vars)[0]
                v_var = list(v_ds.data_vars)[0]
                
                wind_speed = (u_ds[u_var] ** 2 + v_ds[v_var] ** 2) ** 0.5
                
                ws_ds = xr.Dataset({
                    'wind_speed': wind_speed
                })
                ws_ds.attrs['title'] = 'Wind Speed 50m'
                ws_ds.attrs['units'] = 'm/s'
                
                encoding = {'wind_speed': {'zlib': True, 'complevel': 5}}
                ws_ds.to_netcdf(ws50_file, encoding=encoding)
                
                successful_params.append('wind_speed_50m')
                logger.info("Successfully calculated wind_speed_50m")
                
                u_ds.close()
                v_ds.close()
                ws_ds.close()
                
            except Exception as e:
                logger.error(f"Error calculating wind_speed_50m: {e}")
        
        # Generate metadata for all NetCDF files
        logger.info("Generating metadata")
        try:
            all_metadata = generate_layer_metadata(DATA_DIR, METADATA_DIR)
            logger.info(f"Generated metadata for {len(all_metadata)} parameters")
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
        
        # Cleanup old data
        logger.info("Cleaning up old data")
        cleanup_old_data(max_age_hours=72)  # Keep 3 days of data
        
        logger.info("=" * 80)
        logger.info(f"Processing cycle completed successfully")
        logger.info(f"Processed {len(successful_params)} parameters: {', '.join(successful_params)}")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in processing cycle: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def run_periodic_processing():
    """Run processing in a loop with configurable interval"""
    logger.info(f"Starting periodic processing (interval: {FETCH_INTERVAL} seconds)")
    
    # Run immediately on startup
    process_weather_data()
    
    # Then run periodically
    while True:
        try:
            logger.info(f"Sleeping for {FETCH_INTERVAL} seconds until next cycle")
            time.sleep(FETCH_INTERVAL)
            process_weather_data()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down")
            break
        except Exception as e:
            logger.error(f"Error in periodic processing: {e}")
            logger.info("Waiting 5 minutes before retry")
            time.sleep(300)


def main():
    """Main entry point"""
    logger.info("Weather Data Processor starting")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Metadata directory: {METADATA_DIR}")
    logger.info(f"Fetch interval: {FETCH_INTERVAL} seconds")
    logger.info(f"API port: {API_PORT}")
    logger.info(f"Run API: {RUN_API}")
    
    if RUN_API:
        # Start API server in a separate thread
        logger.info("Starting API server in background thread")
        api_thread = threading.Thread(
            target=run_api,
            kwargs={'port': API_PORT, 'debug': False},
            daemon=True
        )
        api_thread.start()
        
        # Give API time to start
        time.sleep(2)
        logger.info(f"API server started on port {API_PORT}")
    
    # Run periodic processing in main thread
    try:
        run_periodic_processing()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
