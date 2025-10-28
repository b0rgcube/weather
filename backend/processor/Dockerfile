FROM python:3.11-slim

# Install system dependencies for GRIB2 and NetCDF
RUN apt-get update && apt-get install -y \
    libeccodes0 \
    libeccodes-dev \
    libnetcdf-dev \
    libhdf5-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/processor/metadata.py .
COPY backend/processor/api.py .
COPY backend/processor/processor.py .

# Copy the existing fetch_weather.py from data-fetcher
COPY backend/data-fetcher/fetch_weather.py /app/fetch_weather.py

# Create data directory
RUN mkdir -p /data/weather/metadata

# Expose API port
EXPOSE 8081

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data/weather
ENV API_PORT=8081
ENV FETCH_INTERVAL=21600

# Run the processor
CMD ["python", "processor.py"]
