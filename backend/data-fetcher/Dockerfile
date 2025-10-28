FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libeccodes-dev \
    libeccodes-tools \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY fetch_weather.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Create data directory
RUN mkdir -p /data/weather

# Run the fetcher
CMD ["./run.sh"]
