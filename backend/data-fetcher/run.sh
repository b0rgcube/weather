#!/bin/bash

# Run script for weather data fetcher
# Runs initial fetch then schedules periodic fetches

echo "Weather Data Fetcher Starting..."

# Get fetch interval from environment (default 6 hours = 21600 seconds)
FETCH_INTERVAL=${FETCH_INTERVAL:-21600}

# Run initial fetch
echo "Running initial data fetch..."
python fetch_weather.py

if [ $? -eq 0 ]; then
    echo "Initial fetch completed successfully"
else
    echo "Initial fetch failed, but continuing..."
fi

# Schedule periodic fetches
echo "Scheduling periodic fetches every $FETCH_INTERVAL seconds"
while true; do
    echo "Sleeping for $FETCH_INTERVAL seconds..."
    sleep $FETCH_INTERVAL
    
    echo "Running scheduled fetch at $(date)"
    python fetch_weather.py
    
    if [ $? -eq 0 ]; then
        echo "Fetch completed successfully"
    else
        echo "Fetch failed, will retry on next interval"
    fi
done
