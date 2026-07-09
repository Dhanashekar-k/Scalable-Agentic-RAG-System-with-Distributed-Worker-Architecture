#!/bin/bash

# ============================================
# Start Niyanta with Monitoring
# ============================================
# This script starts the full Niyanta stack including observability

cd "$(dirname "$0")"

echo "🚀 Starting Niyanta with Monitoring Stack..."
echo ""

# Check if .env exists
if [ ! -f ../.env ]; then
    echo "⚠️  .env file not found, copying from template..."
    cp ./config/.env.example ../.env
    echo ""
    echo "📝 Please edit ../.env with your GROQ_API_KEY before proceeding"
    exit 1
fi

echo "📦 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

echo ""
echo "================================"
echo "✅ Niyanta Started Successfully!"
echo "================================"
echo ""
echo "📊 Access Dashboards:"
echo "   Grafana:       http://localhost:3000 (admin/admin)"
echo "   Prometheus:    http://localhost:9090"
echo "   Backend API:   http://localhost:8000/docs"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:              docker-compose logs -f backend"
echo "   Scale workers:          docker-compose up -d --scale worker=7"
echo "   Check service status:   docker-compose ps"
echo "   View metrics:           curl http://localhost:8000/metrics"
echo ""
echo "📚 Documentation:"
echo "   Full guide:     ./MONITORING.md"
echo "   Setup summary:  ./MONITORING_SETUP_SUMMARY.md"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Go to Dashboards → Niyanta System Overview"
echo "   3. Try queries at http://localhost:8000/docs"
echo ""
echo "Happy monitoring! 📈"
