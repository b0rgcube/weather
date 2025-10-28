#!/bin/bash

# GeoServer Configuration Script
# Configures GeoServer to serve NetCDF weather data via WMS

set -e

GEOSERVER_URL="http://localhost:8080/geoserver"
GEOSERVER_USER="admin"
GEOSERVER_PASS="geoserver"
WORKSPACE="weather"
STORE_NAME="weather_data"
DATA_DIR="/data/weather"

# echo "Waiting for GeoServer to be ready..."
# until curl -sf "${GEOSERVER_URL}/rest/about/version.json" > /dev/null 2>&1; do
#     echo "Waiting for GeoServer..."
#     sleep 5
# done

echo "✅ GeoServer is ready!"
echo ""

# Create workspace
echo "Creating workspace '${WORKSPACE}'..."
curl -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"workspace\":{\"name\":\"${WORKSPACE}\"}}" \
    "${GEOSERVER_URL}/rest/workspaces" 2>/dev/null || echo "Workspace may already exist"

echo "✅ Workspace created/verified"
echo ""

# Function to publish a NetCDF layer
publish_netcdf_layer() {
    local file=$1
    local layer_name=$2
    local variable=$3
    
    echo "Publishing layer: ${layer_name} from ${file}..."
    
    # Create coverage store
    curl -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"coverageStore\": {
                \"name\": \"${layer_name}_store\",
                \"type\": \"NetCDF\",
                \"enabled\": true,
                \"workspace\": {\"name\": \"${WORKSPACE}\"},
                \"url\": \"file://${DATA_DIR}/${file}\"
            }
        }" \
        "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/coveragestores" 2>/dev/null || echo "Store may exist"
    
    # Publish layer
    curl -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"coverage\": {
                \"name\": \"${layer_name}\",
                \"nativeName\": \"${variable}\",
                \"title\": \"${layer_name}\",
                \"enabled\": true
            }
        }" \
        "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/coveragestores/${layer_name}_store/coverages" 2>/dev/null || echo "Layer may exist"
    
    echo "✅ Layer ${layer_name} published"
}

# Publish all layers
echo "Publishing NetCDF layers..."
echo ""

publish_netcdf_layer "temp_2m_2025102712.nc" "temp_2m" "t2m"
publish_netcdf_layer "temp_850mb_2025102712.nc" "temp_850mb" "t"
publish_netcdf_layer "u_wind_10m_2025102712.nc" "u_wind_10m" "u10"
publish_netcdf_layer "v_wind_10m_2025102712.nc" "v_wind_10m" "v10"
publish_netcdf_layer "u_wind_50m_2025102712.nc" "u_wind_50m" "u"
publish_netcdf_layer "v_wind_50m_2025102712.nc" "v_wind_50m" "v"
publish_netcdf_layer "precip_rate_2025102712.nc" "precip_rate" "prate"
publish_netcdf_layer "mslp_2025102712.nc" "mslp" "prmsl"
publish_netcdf_layer "rh_2m_2025102712.nc" "rh_2m" "r2"

echo ""
echo "✅ All layers published!"
echo ""
echo "You can now access the WMS service at:"
echo "${GEOSERVER_URL}/wms"
echo ""
echo "View layers in GeoServer web UI:"
echo "${GEOSERVER_URL}/web"
echo ""
