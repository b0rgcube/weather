# Quick Start Guide

Get the Weather Visualization System up and running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Docker installed (version 20.10+)
- ✅ Docker Compose installed (version 2.0+)
- ✅ 4GB+ RAM available
- ✅ 10GB+ free disk space
- ✅ Internet connection

## Option 1: Automated Setup (Recommended)

### Linux/macOS

```bash
# Run the setup script
./start.sh
```

### Windows

```bash
# Create data directory
mkdir data\weather

# Copy environment file
copy .env.example .env

# Start services
docker-compose up -d

# Follow logs
docker-compose logs -f data-fetcher
```

## Option 2: Manual Setup

### Step 1: Prepare Environment

```bash
# Create data directory
mkdir -p data/weather

# Copy environment configuration
cp .env.example .env
```

### Step 2: Start Services

```bash
# Start all services in detached mode
docker-compose up -d
```

### Step 3: Monitor Initial Data Download

```bash
# Watch the data fetcher logs
docker-compose logs -f data-fetcher
```

**Wait 15-30 minutes** for the initial data download to complete.

### Step 4: Access Application

Once you see "Weather data fetch completed" in the logs, open your browser:

```
http://localhost
```

## What to Expect

### During First Launch

1. **Minute 1-2**: Docker images download
2. **Minute 2-3**: Services initialize
3. **Minute 3-30**: Weather data downloads from NOAA
4. **After 30 min**: Application ready to use!

### Normal Operation

After the first launch, the system:
- Automatically downloads new data every 6 hours
- Keeps 48 hours of forecast data
- Serves data immediately (no waiting)

## Quick Commands

### Check Services Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f data-fetcher
docker-compose logs -f ncwms
docker-compose logs -f nginx
```

### Stop System
```bash
docker-compose down
```

### Restart System
```bash
docker-compose restart
```

### Force Data Update
```bash
docker-compose exec data-fetcher python fetch_weather.py
```

## Using the Application

### Basic Controls

1. **Select Weather Parameter**
   - Use dropdown menu to choose (Temperature, Wind, etc.)

2. **Play Animation**
   - Click Play button or press `Space`
   - Adjust speed: 0.5x, 1x, 2x, 4x

3. **Navigate Timeline**
   - Drag slider
   - Use arrow keys: `←` previous, `→` next

4. **Adjust Display**
   - Opacity slider: 0-100%
   - Toggle layer: On/Off checkbox

5. **Dark Mode**
   - Click moon/sun icon in header

### Keyboard Shortcuts

- `Space` - Play/Pause animation
- `←` - Previous frame
- `→` - Next frame  
- `Esc` - Stop animation

## Troubleshooting

### "No weather data available"

**Solution**: Wait for data download to complete
```bash
docker-compose logs -f data-fetcher
```

### Port Already in Use

**Solutions**:
```bash
# Check what's using port 80
sudo lsof -i :80

# Or change port in docker-compose.yml
# Change "80:80" to "8000:80"
```

### Services Won't Start

**Solutions**:
```bash
# Clean restart
docker-compose down -v
docker-compose up -d

# Check Docker resources
docker system df
```

### Application Loads but No Map

**Solutions**:
1. Check browser console (F12)
2. Verify ncWMS2 is running:
   ```bash
   curl http://localhost:8080/ncWMS2/
   ```
3. Clear browser cache

## Performance Tips

### For Slower Computers

Edit `backend/data-fetcher/fetch_weather.py`:
```python
# Reduce forecast hours (line ~149)
forecast_hours = list(range(0, 25, 6))  # 0-24hrs only

# Reduce data retention (line ~241)
cleanup_old_data(max_age_hours=24)  # Keep only 24hrs
```

### For Limited Bandwidth

Edit `docker-compose.yml`:
```yaml
environment:
  - FETCH_INTERVAL=43200  # Every 12 hours instead of 6
```

## Next Steps

- 📖 Read full [README.md](README.md) for detailed documentation
- 🎨 Customize color scales in `backend/config/ncwms-config.xml`
- 🗺️ Explore different weather parameters
- 📱 Try on tablet/mobile device

## Getting Help

1. Check logs: `docker-compose logs`
2. Review [README.md](README.md) troubleshooting section
3. Verify prerequisites are met
4. Try clean restart: `docker-compose down && docker-compose up -d`

## Success Indicators

You'll know everything is working when:
- ✅ All three services show "Up" in `docker-compose ps`
- ✅ Data fetcher logs show "Weather data fetch completed"
- ✅ Browser shows animated weather map at `http://localhost`
- ✅ You can play/pause the animation
- ✅ Weather parameter dropdown works
- ✅ Legend updates when changing parameters

**Enjoy your weather visualization system! 🌤️**
