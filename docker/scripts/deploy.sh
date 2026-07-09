#!/bin/bash

# ==========================================
# Niyanta Deployment Script
# ==========================================
# One-command deployment for production

set -e  # Exit on error

echo "🚀 Niyanta Deployment Started..."
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ../../.env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "📝 Creating .env from ../config/.env.example..."
    cp ../config/.env.example ../../.env
    echo -e "${YELLOW}⚠️  Please edit .env with your configuration before continuing.${NC}"
    echo "   Required: GROQ_API_KEY, ADMIN_PASSWORD, NEO4J_PASSWORD"
    exit 1
fi

# Check if required variables are set
echo "🔍 Checking environment variables..."
source ../../.env

if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
    echo -e "${RED}❌ GROQ_API_KEY not set in .env${NC}"
    exit 1
fi

if [ "$ADMIN_PASSWORD" = "admin" ]; then
    echo -e "${YELLOW}⚠️  Warning: Using default ADMIN_PASSWORD - change in production${NC}"
fi

echo -e "${GREEN}✓ Environment variables configured${NC}"

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose -f ../docker-compose.yml down

# Pull latest images
echo ""
echo "📦 Pulling base images..."
docker-compose -f ../docker-compose.yml pull redis rabbitmq

# Build application images
echo ""
echo "🏗️  Building application images..."
docker-compose -f ../docker-compose.yml build --no-cache

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose -f ../docker-compose.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Health check..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f ../docker-compose.yml ps | grep -q "unhealthy"; then
        echo -e "${YELLOW}⏳ Services starting... (attempt $((attempt+1))/$max_attempts)${NC}"
        sleep 5
        attempt=$((attempt+1))
    else
        echo -e "${GREEN}✓ All services healthy${NC}"
        break
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Some services failed to start${NC}"
    docker-compose -f ../docker-compose.yml ps
    exit 1
fi

# Show running services
echo ""
echo "📊 Running services:"
docker-compose -f ../docker-compose.yml ps

echo ""
echo "================================"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "🌐 Access points:"
echo "   Backend API:      http://localhost:8000"
echo "   API Docs:         http://localhost:8000/docs"
echo "   RabbitMQ:         http://localhost:15672 (guest/guest)"
echo "   Redis:            localhost:6379"
echo ""
echo "🎛️  Optional services (if enabled in docker-compose.yml):"
echo "   Neo4j Browser:    http://localhost:7474"
echo "   ChromaDB:         http://localhost:8001"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        ./scripts/logs.sh"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Scale workers:    docker-compose up -d --scale worker=7"
echo "   Scale to 10:      docker-compose up -d --scale worker=10"
echo ""
echo "📍 Frontend:"
echo "   Run locally:      cd ../frontend && npm run dev"
echo "   Access:           http://localhost:5173"
echo ""
echo "🎉 Happy coding!"
