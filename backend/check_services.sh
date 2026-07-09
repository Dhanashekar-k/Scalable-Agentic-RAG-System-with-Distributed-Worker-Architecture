#!/bin/bash

# Service Status Checker
# Verifies that Redis, RabbitMQ, and Neo4j are running

echo "🔍 Checking Service Status..."
echo "=============================="
echo ""

ALL_OK=true

# Check Redis
echo -n "Redis (port 6379)....... "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    ALL_OK=false
fi

# Check RabbitMQ
echo -n "RabbitMQ (port 5672).... "
if nc -z localhost 5672 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    ALL_OK=false
fi

# Check RabbitMQ Management UI
echo -n "RabbitMQ UI (port 15672). "
if curl -s http://localhost:15672 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "⚠️  Management UI not ready"
fi

# Check Neo4j HTTP
echo -n "Neo4j HTTP (port 7474).. "
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    ALL_OK=false
fi

# Check Neo4j Bolt
echo -n "Neo4j Bolt (port 7687).. "
if nc -z localhost 7687 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    ALL_OK=false
fi

echo ""
echo "=============================="

if [ "$ALL_OK" = true ]; then
    echo "✅ All services are running!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Make sure .env is configured with GROQ_API_KEY"
    echo "2. Run: python main.py (Terminal 1)"
    echo "3. Run: python worker_main.py (Terminal 2)"
    exit 0
else
    echo "❌ Some services are not running"
    echo ""
    echo "🛠️  To start services:"
    echo ""
    echo "macOS:"
    echo "  brew services start redis"
    echo "  brew services start rabbitmq"
    echo "  brew services start neo4j"
    echo ""
    echo "Linux:"
    echo "  sudo systemctl start redis"
    echo "  sudo systemctl start rabbitmq-server"
    echo "  sudo systemctl start neo4j"
    exit 1
fi
