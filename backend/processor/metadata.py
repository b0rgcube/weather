#!/usr/bin/env python3
"""
Metadata generation for weather data
Creates JSON metadata files for the WMS server
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import xarray as xr
import numpy as np

logger = logging.getLogger(__name__)

# Color scale definitions for each parameter
COLOR_SCALES = {
    'temp_2m': {
        'name': 'Temperature 2m',
        'units': '°C',
        'palette': 'rainbow',
        'range': [-40, 50],
        'colors': [
            {'value': -40, 'color': '#000080'},
            {'value': -20, 'color': '#0000FF'},
            {'value': 0, 'color': '#00FFFF'},
            {'value': 10, 'color': '#00FF00'},
            {'value': 20, 'color': '#FFFF00'},
            {'value': 30, 'color': '#FF8000'},
            {'value': 40, 'color': '#FF0000'},
            {'value': 50, 'color': '#800000'}
        ]
    },
    'temp_850mb': {
        'name': 'Temperature 850mb',
        'units': '°C',
        'palette': 'rainbow',
        'range': [-60, 30],
        'colors': [
            {'value': -60, 'color': '#000080'},
            {'value': -40, 'color': '#0000FF'},
            {'value': -20, 'color': '#00FFFF'},
            {'value': 0, 'color': '#00FF00'},
            {'value': 10, 'color': '#FFFF00'},
            {'value': 20, 'color': '#FF8000'},
            {'value': 30, 'color': '#FF0000'}
        ]
    },
    'wind_speed_10m': {
        'name': 'Wind Speed 10m',
        'units': 'm/s',
        'palette': 'wind',
        'range': [0, 30],
        'colors': [
            {'value': 0, 'color': '#FFFFFF'},
            {'value': 5, 'color': '#00FF00'},
            {'value': 10, 'color': '#FFFF00'},
            {'value': 15, 'color': '#FF8000'},
            {'value': 20, 'color': '#FF0000'},
            {'value': 25, 'color': '#800000'},
            {'value': 30, 'color': '#400000'}
        ]
    },
    'wind_speed_50m': {
        'name': 'Wind Speed 50m',
        'units': 'm/s',
        'palette': 'wind',
        'range': [0, 40],
        'colors': [
            {'value': 0, 'color': '#FFFFFF'},
            {'value': 10, 'color': '#00FF00'},
            {'value': 20, 'color': '#FFFF00'},
            {'value': 30, 'color': '#FF0000'},
            {'value': 40, 'color': '#800000'}
        ]
    },
    'precip_rate': {
        'name': 'Precipitation Rate',
        'units': 'mm/hr',
        'palette': 'precipitation',
        'range': [0, 20],
        'colors': [
            {'value': 0, 'color': '#FFFFFF'},
            {'value': 0.1, 'color': '#C0E0FF'},
            {'value': 1, 'color': '#00FF00'},
            {'value': 5, 'color': '#FFFF00'},
            {'value': 10, 'color': '#FF8000'},
            {'value': 15, 'color': '#FF0000'},
            {'value': 20, 'color': '#800000'}
        ]
    },
    'mslp': {
        'name': 'Mean Sea Level Pressure',
        'units': 'hPa',
        'palette': 'pressure',
        'range': [960, 1040],
        'colors': [
            {'value': 960, 'color': '#FF0000'},
            {'value': 980, 'color': '#FF8000'},
            {'value': 1000, 'color': '#FFFF00'},
            {'value': 1013, 'color': '#00FF00'},
            {'value': 1020, 'color': '#00FFFF'},
            {'value': 1030, 'color': '#0000FF'},
            {'value': 1040, 'color': '#000080'}
        ]
    },
    'rh_2m': {
        'name': 'Relative Humidity 2m',
        'units': '%',
        'palette': 'humidity',
        'range': [0, 100],
        'colors': [
            {'value': 0, 'color': '#8B4513'},
            {'value': 20, 'color': '#FFD700'},
            {'value': 40, 'color': '#FFFF00'},
            {'value': 60, 'color': '#00FF00'},
            {'value': 80, 'color': '#00FFFF'},
            {'value': 100, 'color': '#0000FF'}
        ]
    }
}


def extract_metadata_from_netcdf(nc_file: Path, param_name: str) -> Dict[str, Any]:
    """
    Extract metadata from a NetCDF file
    
    Args:
        nc_file: Path to NetCDF file
        param_name: Parameter name (e.g., 'temp_2m')
    
    Returns:
        Dictionary containing metadata
    """
    try:
        logger.info(f"Extracting metadata from {nc_file}")
        
        with xr.open_dataset(nc_file) as ds:
            # Get variable name (first data variable)
            var_name = list(ds.data_vars)[0]
            var = ds[var_name]
            
            # Extract time dimension
            times = []
            if 'time' in ds.coords:
                time_values = ds.time.values
                for t in time_values:
                    # Convert numpy datetime64 to ISO string
                    dt = np.datetime64(t, 'ns').astype('datetime64[s]').astype(datetime)
                    times.append(dt.isoformat() + 'Z')
            
            # Extract spatial bounds
            lat = ds.latitude.values if 'latitude' in ds.coords else ds.lat.values
            lon = ds.longitude.values if 'longitude' in ds.coords else ds.lon.values
            
            bounds = {
                'north': float(np.max(lat)),
                'south': float(np.min(lat)),
                'east': float(np.max(lon)),
                'west': float(np.min(lon))
            }
            
            # Calculate data statistics
            data_min = float(var.min().values)
            data_max = float(var.max().values)
            data_mean = float(var.mean().values)
            
            # Get color scale info
            color_scale = COLOR_SCALES.get(param_name, {
                'name': param_name,
                'units': 'unknown',
                'palette': 'rainbow',
                'range': [data_min, data_max],
                'colors': []
            })
            
            metadata = {
                'parameter': param_name,
                'name': color_scale['name'],
                'units': color_scale['units'],
                'file': str(nc_file.name),
                'variable': var_name,
                'times': times,
                'bounds': bounds,
                'statistics': {
                    'min': data_min,
                    'max': data_max,
                    'mean': data_mean
                },
                'colorScale': color_scale,
                'dimensions': {
                    'time': len(times),
                    'lat': len(lat),
                    'lon': len(lon)
                },
                'created': datetime.utcnow().isoformat() + 'Z'
            }
            
            return metadata
            
    except Exception as e:
        logger.error(f"Error extracting metadata from {nc_file}: {e}")
        raise


def generate_layer_metadata(data_dir: Path, metadata_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate metadata for all available layers
    
    Args:
        data_dir: Directory containing NetCDF files
        metadata_dir: Directory to save metadata JSON files
    
    Returns:
        Dictionary mapping parameter names to list of metadata
    """
    logger.info("Generating layer metadata")
    
    metadata_dir.mkdir(parents=True, exist_ok=True)
    all_metadata = {}
    
    # Group NetCDF files by parameter
    for nc_file in data_dir.glob('*.nc'):
        # Extract parameter name from filename (e.g., temp_2m_2024010100.nc -> temp_2m)
        parts = nc_file.stem.split('_')
        if len(parts) >= 2:
            # Handle multi-part parameter names like wind_speed_10m
            if parts[0] == 'wind' and parts[1] == 'speed':
                param_name = f"{parts[0]}_{parts[1]}_{parts[2]}"
            else:
                # For simple names like temp_2m, temp_850mb
                param_name = '_'.join(parts[:-1])  # Everything except the timestamp
        else:
            param_name = nc_file.stem
        
        try:
            metadata = extract_metadata_from_netcdf(nc_file, param_name)
            
            if param_name not in all_metadata:
                all_metadata[param_name] = []
            
            all_metadata[param_name].append(metadata)
            
        except Exception as e:
            logger.error(f"Failed to process {nc_file}: {e}")
            continue
    
    # Save metadata for each parameter
    for param_name, metadata_list in all_metadata.items():
        # Sort by creation time (most recent first)
        metadata_list.sort(key=lambda x: x['created'], reverse=True)
        
        metadata_file = metadata_dir / f"{param_name}.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'parameter': param_name,
                'datasets': metadata_list,
                'count': len(metadata_list),
                'updated': datetime.utcnow().isoformat() + 'Z'
            }, f, indent=2)
        
        logger.info(f"Saved metadata for {param_name} to {metadata_file}")
    
    # Save master index
    index_file = metadata_dir / 'index.json'
    with open(index_file, 'w') as f:
        json.dump({
            'parameters': list(all_metadata.keys()),
            'count': len(all_metadata),
            'updated': datetime.utcnow().isoformat() + 'Z',
            'colorScales': COLOR_SCALES
        }, f, indent=2)
    
    logger.info(f"Saved master index to {index_file}")
    
    return all_metadata


def get_capabilities_xml(all_metadata: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Generate WMS GetCapabilities XML response
    
    Args:
        all_metadata: Dictionary of all layer metadata
    
    Returns:
        XML string for GetCapabilities response
    """
    # Collect all unique times across all layers
    all_times = set()
    for metadata_list in all_metadata.values():
        for metadata in metadata_list:
            all_times.update(metadata['times'])
    
    time_list = sorted(list(all_times))
    time_extent = f"{time_list[0]}/{time_list[-1]}/PT3H" if time_list else ""
    
    # Build layer XML
    layers_xml = []
    for param_name, metadata_list in all_metadata.items():
        if not metadata_list:
            continue
        
        latest = metadata_list[0]
        bounds = latest['bounds']
        
        layer_xml = f"""
    <Layer queryable="1">
      <Name>{param_name}</Name>
      <Title>{latest['name']}</Title>
      <Abstract>Weather parameter: {latest['name']} ({latest['units']})</Abstract>
      <CRS>EPSG:4326</CRS>
      <CRS>EPSG:3857</CRS>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>{bounds['west']}</westBoundLongitude>
        <eastBoundLongitude>{bounds['east']}</eastBoundLongitude>
        <southBoundLatitude>{bounds['south']}</southBoundLatitude>
        <northBoundLatitude>{bounds['north']}</northBoundLatitude>
      </EX_GeographicBoundingBox>
      <BoundingBox CRS="EPSG:4326" 
                   minx="{bounds['west']}" miny="{bounds['south']}" 
                   maxx="{bounds['east']}" maxy="{bounds['north']}"/>
      <Dimension name="time" units="ISO8601">{time_extent}</Dimension>
      <Style>
        <Name>default</Name>
        <Title>Default Style</Title>
      </Style>
    </Layer>"""
        layers_xml.append(layer_xml)
    
    capabilities = f"""<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd">
  <Service>
    <Name>WMS</Name>
    <Title>Weather Visualization WMS Server</Title>
    <Abstract>Custom WMS server for NOAA GFS weather data</Abstract>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8080/wms"/>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
        <DCPType>
          <HTTP>
            <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8080/wms?"/></Get>
          </HTTP>
        </DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType>
          <HTTP>
            <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8080/wms?"/></Get>
          </HTTP>
        </DCPType>
      </GetMap>
      <GetFeatureInfo>
        <Format>application/json</Format>
        <DCPType>
          <HTTP>
            <Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8080/wms?"/></Get>
          </HTTP>
        </DCPType>
      </GetFeatureInfo>
    </Request>
    <Exception>
      <Format>XML</Format>
      <Format>JSON</Format>
    </Exception>
    <Layer>
      <Title>Weather Data Layers</Title>
      <CRS>EPSG:4326</CRS>
      <CRS>EPSG:3857</CRS>
      {''.join(layers_xml)}
    </Layer>
  </Capability>
</WMS_Capabilities>"""
    
    return capabilities


if __name__ == '__main__':
    # Test metadata generation
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python metadata.py <data_dir>")
        sys.exit(1)
    
    data_dir = Path(sys.argv[1])
    metadata_dir = data_dir / 'metadata'
    
    all_metadata = generate_layer_metadata(data_dir, metadata_dir)
    print(f"Generated metadata for {len(all_metadata)} parameters")
