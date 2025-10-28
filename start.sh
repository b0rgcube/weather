#!/bin/bash

# Weather Visualization System - Quick Start Script
# This script helps set up and start the weather visualization system

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║   Weather Visualization System - Quick Start          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data/weather
echo "✅ Data directory created"
echo ""

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created (you can customize it if needed)"
else
    echo "✅ .env file already exists"
fi
echo ""

# Ask user if they want to start the services
read -p "🚀 Start the weather visualization system? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting services..."
    echo "This will take a few moments on first run (downloading Docker images)..."
    echo ""
    
    # Start services
    docker-compose up -d
    
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║              Services Status                           ║"
    echo "╚════════════════════════════════════════════════════════╝"
    docker-compose ps
    echo ""
    
    echo "📊 Next Steps:"
    echo ""
    echo "1. Monitor data fetcher (this will take 15-30 minutes for first download):"
    echo "   docker-compose logs -f data-fetcher"
    echo ""
    echo "2. Once data is downloaded, access the application:"
    echo "   http://localhost"
    echo ""
    echo "3. To stop the system:"
    echo "   docker-compose down"
    echo ""
    echo "4. To view all logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
    
    # Ask if user wants to follow logs
    read -p "📋 Would you like to follow the data fetcher logs now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Following logs (press Ctrl+C to exit)..."
        echo ""
        docker-compose logs -f data-fetcher
    fi
else
    echo ""
    echo "Setup complete! To start the system later, run:"
    echo "  docker-compose up -d"
    echo ""
fi
