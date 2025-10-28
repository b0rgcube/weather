#!/usr/bin/env python3
"""
HTTP API for weather data metadata
Provides endpoints for the WMS server to query metadata
"""

import json
import logging
from pathlib import Path
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from typing import Dict, Any
import io
import numpy as np
import xarray as xr
from PIL import Image
import os

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_DIR = Path(os.getenv('DATA_DIR', '/data/weather'))
METADATA_DIR = DATA_DIR / 'metadata'


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'weather-processor-api',
        'data_dir': str(DATA_DIR),
        'metadata_dir': str(METADATA_DIR)
    })


@app.route('/api/metadata', methods=['GET'])
def get_all_metadata():
    """Get metadata for all parameters"""
    try:
        index_file = METADATA_DIR / 'index.json'
        
        if not index_file.exists():
            return jsonify({
                'error': 'No metadata available',
                'message': 'Metadata has not been generated yet'
            }), 404
        
        with open(index_file, 'r') as f:
            index_data = json.load(f)
        
        return jsonify(index_data)
        
    except Exception as e:
        logger.error(f"Error reading metadata index: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/metadata/<parameter>', methods=['GET'])
def get_parameter_metadata(parameter: str):
    """Get metadata for a specific parameter"""
    try:
        metadata_file = METADATA_DIR / f"{parameter}.json"
        
        if not metadata_file.exists():
            return jsonify({
                'error': 'Parameter not found',
                'parameter': parameter
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata)
        
    except Exception as e:
        logger.error(f"Error reading metadata for {parameter}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/capabilities', methods=['GET'])
def get_capabilities():
    """Get WMS GetCapabilities XML"""
    try:
        from metadata import generate_layer_metadata, get_capabilities_xml
        
        # Generate fresh metadata
        all_metadata = {}
        for metadata_file in METADATA_DIR.glob('*.json'):
            if metadata_file.name == 'index.json':
                continue
            
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                if 'parameter' in data and 'datasets' in data:
                    all_metadata[data['parameter']] = data['datasets']
        
        if not all_metadata:
            return Response(
                '<?xml version="1.0"?><error>No data available</error>',
                mimetype='text/xml',
                status=404
            )
        
        capabilities_xml = get_capabilities_xml(all_metadata)
        return Response(capabilities_xml, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error generating capabilities: {e}")
        return Response(
            f'<?xml version="1.0"?><error>{str(e)}</error>',
            mimetype='text/xml',
            status=500
        )


@app.route('/api/layers', methods=['GET'])
def get_layers():
    """Get list of available layers"""
    try:
        index_file = METADATA_DIR / 'index.json'
        
        if not index_file.exists():
            return jsonify({
                'layers': [],
                'count': 0
            })
        
        with open(index_file, 'r') as f:
            index_data = json.load(f)
        
        layers = []
        for param in index_data.get('parameters', []):
            metadata_file = METADATA_DIR / f"{param}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    param_data = json.load(f)
                    if param_data.get('datasets'):
                        latest = param_data['datasets'][0]
                        layers.append({
                            'name': param,
                            'title': latest.get('name', param),
                            'units': latest.get('units', ''),
                            'bounds': latest.get('bounds', {}),
                            'times': latest.get('times', []),
                            'colorScale': latest.get('colorScale', {})
                        })
        
        return jsonify({
            'layers': layers,
            'count': len(layers)
        })
        
    except Exception as e:
        logger.error(f"Error getting layers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/layer/<layer_name>/times', methods=['GET'])
def get_layer_times(layer_name: str):
    """Get available time steps for a layer"""
    try:
        metadata_file = METADATA_DIR / f"{layer_name}.json"
        
        if not metadata_file.exists():
            return jsonify({
                'error': 'Layer not found',
                'layer': layer_name
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Collect all unique times from all datasets
        all_times = set()
        for dataset in metadata.get('datasets', []):
            all_times.update(dataset.get('times', []))
        
        times = sorted(list(all_times))
        
        return jsonify({
            'layer': layer_name,
            'times': times,
            'count': len(times)
        })
        
    except Exception as e:
        logger.error(f"Error getting times for {layer_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/layer/<layer_name>/bounds', methods=['GET'])
def get_layer_bounds(layer_name: str):
    """Get geographic bounds for a layer"""
    try:
        metadata_file = METADATA_DIR / f"{layer_name}.json"
        
        if not metadata_file.exists():
            return jsonify({
                'error': 'Layer not found',
                'layer': layer_name
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if not metadata.get('datasets'):
            return jsonify({
                'error': 'No datasets available',
                'layer': layer_name
            }), 404
        
        bounds = metadata['datasets'][0].get('bounds', {})
        
        return jsonify({
            'layer': layer_name,
            'bounds': bounds
        })
        
    except Exception as e:
        logger.error(f"Error getting bounds for {layer_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/layer/<layer_name>/colorscale', methods=['GET'])
def get_layer_colorscale(layer_name: str):
    """Get color scale for a layer"""
    try:
        metadata_file = METADATA_DIR / f"{layer_name}.json"
        
        if not metadata_file.exists():
            return jsonify({
                'error': 'Layer not found',
                'layer': layer_name
            }), 404
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if not metadata.get('datasets'):
            return jsonify({
                'error': 'No datasets available',
                'layer': layer_name
            }), 404
        
        colorscale = metadata['datasets'][0].get('colorScale', {})
        
        return jsonify({
            'layer': layer_name,
            'colorScale': colorscale
        })
        
    except Exception as e:
        logger.error(f"Error getting colorscale for {layer_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def list_netcdf_files():
    """List available NetCDF files"""
    try:
        files = []
        for nc_file in DATA_DIR.glob('*.nc'):
            stat = nc_file.stat()
            files.append({
                'name': nc_file.name,
                'size': stat.st_size,
                'modified': stat.st_mtime
            })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'files': files,
            'count': len(files),
            'directory': str(DATA_DIR)
        })
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/render', methods=['GET'])
def render_layer():
    """
    Render a PNG for a given layer from NetCDF.
    Query params:
      - layer: parameter name (e.g., temp_2m, wind_speed_10m) [required]
      - file: optional specific NetCDF filename (relative to DATA_DIR)
      - time: optional ISO8601 timestamp to select nearest time slice
      - bbox: minx,miny,maxx,maxy (in lon/lat degrees, EPSG:4326)
      - width, height: output image size in pixels (defaults 256x256)
      - colorscalerange: "min,max" numeric range for color mapping
    Notes:
      - CRS currently assumed to be EPSG:4326 (lon/lat)
      - If bbox omitted, full extent is rendered
    """
    try:
        layer = request.args.get('layer')
        if not layer:
            return jsonify({'error': 'Missing layer parameter'}), 400

        file_param = request.args.get('file')
        time_str = request.args.get('time')
        bbox_str = request.args.get('bbox')
        width = int(request.args.get('width', 256))
        height = int(request.args.get('height', 256))
        csr = request.args.get('colorscalerange')
        palette_name = request.args.get('palette') or request.args.get('styles') or 'rainbow'
        # Optional gamma for contrast tuning (default 1.0 = linear). Values < 1 increase contrast.
        try:
            gamma = float(request.args.get('gamma', 1.0))
        except Exception:
            gamma = 1.0

        # Resolve NetCDF file path
        nc_path = None
        if file_param:
            # Sanitize simple relative file names
            fp = Path(file_param)
            nc_path = (DATA_DIR / fp.name) if not fp.is_absolute() else fp
        else:
            # Pick latest for this layer
            candidates = sorted(DATA_DIR.glob(f"{layer}_*.nc"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                nc_path = candidates[0]

        if not nc_path or not nc_path.exists():
            # Fallback: if requested file missing, use latest file for this layer
            candidates = sorted(DATA_DIR.glob(f"{layer}_*.nc"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                nc_path = candidates[0]
            else:
                return jsonify({'error': 'NetCDF file not found for layer', 'layer': layer}), 404

        with xr.open_dataset(nc_path) as ds:
            # Find primary variable
            if not ds.data_vars:
                return jsonify({'error': 'No data variables in dataset', 'file': nc_path.name}), 500
            var_name = list(ds.data_vars)[0]
            var = ds[var_name]

            # Select time slice
            if 'time' in ds.coords and var.ndim >= 3:
                if time_str:
                    try:
                        # nearest selection
                        var = var.sel(time=np.datetime64(time_str), method='nearest')
                    except Exception:
                        # fallback to first time
                        var = var.isel(time=0)
                else:
                    var = var.isel(time=0)

            # Determine coordinate names
            lat_name = 'latitude' if 'latitude' in var.coords else ('lat' if 'lat' in var.coords else None)
            lon_name = 'longitude' if 'longitude' in var.coords else ('lon' if 'lon' in var.coords else None)
            if not lat_name or not lon_name:
                return jsonify({'error': 'Could not determine latitude/longitude coordinates'}), 500

            lats = var[lat_name].values
            lons = var[lon_name].values

            # Normalize longitude to [-180,180] range for bbox comparison if necessary
            # Many GFS files use 0..360; convert to -180..180
            lons_norm = lons.copy()
            if np.nanmax(lons) > 180.0:
                lons_norm = ((lons + 180.0) % 360.0) - 180.0

            # Ensure latitude ascending for indexing
            flip_lat = False
            if lats[0] > lats[-1]:
                flip_lat = True
                lats = lats[::-1]
                var = var[::-1, :] if var.ndim == 2 else var[::-1, :, :]

            # Subset by bbox if provided
            if bbox_str:
                try:
                    minx, miny, maxx, maxy = [float(v) for v in bbox_str.split(',')]
                    # Clip to dataset bounds
                    minx, maxx = max(minx, float(np.nanmin(lons_norm))), min(maxx, float(np.nanmax(lons_norm)))
                    miny, maxy = max(miny, float(np.nanmin(lats))),     min(maxy, float(np.nanmax(lats)))

                    # Compute index ranges
                    lon_idx_min = int(np.clip(np.searchsorted(lons_norm, minx, side='left'), 0, len(lons_norm)-1))
                    lon_idx_max = int(np.clip(np.searchsorted(lons_norm, maxx, side='right') - 1, 0, len(lons_norm)-1))
                    lat_idx_min = int(np.clip(np.searchsorted(lats, miny, side='left'), 0, len(lats)-1))
                    lat_idx_max = int(np.clip(np.searchsorted(lats, maxy, side='right') - 1, 0, len(lats)-1))

                    if var.ndim == 2:
                        var = var.isel({lat_name: slice(lat_idx_min, lat_idx_max+1),
                                        lon_name: slice(lon_idx_min, lon_idx_max+1)})
                    elif var.ndim == 3:
                        # var dims likely (time, lat, lon) and already sliced time
                        var = var.isel({lat_name: slice(lat_idx_min, lat_idx_max+1),
                                        lon_name: slice(lon_idx_min, lon_idx_max+1)})
                except Exception as e:
                    logger.warning(f"Invalid bbox '{bbox_str}': {e}")

            # Obtain 2D array
            data = var.values
            if data.ndim == 3:
                # If still 3D for some reason, take first slice
                data = data[0, :, :]
            data = np.array(data, dtype=np.float32)

            # Handle NaNs
            mask = np.isfinite(data)
            if not np.any(mask):
                # No valid data
                blank = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                buf = io.BytesIO()
                blank.save(buf, format='PNG')
                return Response(buf.getvalue(), mimetype='image/png')

            # Determine color scale range
            if csr:
                try:
                    vmin, vmax = [float(x) for x in csr.split(',')]
                except Exception:
                    vmin, vmax = (float(np.nanpercentile(data, 2)), float(np.nanpercentile(data, 98)))
            else:
                vmin, vmax = (float(np.nanpercentile(data, 2)), float(np.nanpercentile(data, 98)))
            if vmax <= vmin:
                vmax = vmin + 1.0

            # Normalize 0..255
            norm = (data - vmin) / (vmax - vmin)
            norm = np.clip(norm, 0.0, 1.0)
            idx = (np.power(norm, gamma) * 255).astype(np.uint8)

            # Build a high-contrast palette (rainbow-like) or grayscale if requested
            def _interp_color(c1, c2, t):
                return (
                    int(c1[0] + (c2[0] - c1[0]) * t),
                    int(c1[1] + (c2[1] - c1[1]) * t),
                    int(c1[2] + (c2[2] - c1[2]) * t),
                )

            if palette_name and palette_name.lower() == 'grayscale':
                palette = np.stack([np.arange(256, dtype=np.uint8)] * 3, axis=1)  # 256x3 grayscale
            else:
                # Select palette: 'windy' (purple->blue->cyan->green->yellow->orange->red->white) or default rainbow
                if palette_name and palette_name.lower() in ('windy', 'wind'):
                    stops = [
                        (0.00, (68, 0, 85)),     # deep purple
                        (0.15, (0, 0, 130)),     # dark blue
                        (0.30, (0, 0, 255)),     # blue
                        (0.45, (0, 255, 255)),   # cyan
                        (0.60, (0, 255, 0)),     # green
                        (0.75, (255, 255, 0)),   # yellow
                        (0.90, (255, 128, 0)),   # orange
                        (1.00, (255, 255, 255)), # white (hot extreme)
                    ]
                else:
                    # High-contrast rainbow-style stops
                    stops = [
                        (0.00, (0, 0, 130)),     # dark blue
                        (0.20, (0, 0, 255)),     # blue
                        (0.40, (0, 255, 255)),   # cyan
                        (0.60, (0, 255, 0)),     # green
                        (0.80, (255, 255, 0)),   # yellow
                        (1.00, (255, 0, 0)),     # red
                    ]
                palette = np.zeros((256, 3), dtype=np.uint8)
                for i in range(256):
                    t = i / 255.0
                    for s in range(len(stops) - 1):
                        t0, c0 = stops[s]
                        t1, c1 = stops[s + 1]
                        if t <= t1 or s == len(stops) - 2:
                            lt = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                            palette[i] = _interp_color(c0, c1, lt)
                            break

            # Create RGBA, transparent where NaN
            rgba = np.zeros((idx.shape[0], idx.shape[1], 4), dtype=np.uint8)
            rgba[..., :3] = palette[idx]
            rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)

            img = Image.fromarray(rgba, mode='RGBA')
            if img.size != (width, height):
                img = img.resize((width, height), Image.BILINEAR)

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return Response(buf.getvalue(), mimetype='image/png')

    except Exception as e:
        logger.error(f"Error rendering layer: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


def run_api(host='0.0.0.0', port=8081, debug=False):
    """Run the API server"""
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Metadata directory: {METADATA_DIR}")
    
    # Ensure metadata directory exists
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    port = int(os.getenv('API_PORT', 8081))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    run_api(port=port, debug=debug)
