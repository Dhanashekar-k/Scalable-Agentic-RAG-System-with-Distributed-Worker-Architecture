#!/bin/bash

# Hybrid Setup - Docker for Redis/RabbitMQ, Native Neo4j
# Best of both worlds approach

set -e

echo "🎯 Hybrid Setup - Redis/RabbitMQ (Docker) + Neo4j (Native)"
echo "=========================================================="
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Darwin*)    OS_TYPE="macOS";;
    Linux*)     OS_TYPE="Linux";;
    *)          OS_TYPE="UNKNOWN";;
esac

echo "📍 Detected OS: $OS_TYPE"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first:"
    echo "   macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "   Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✅ Docker found"
echo ""

# Start Redis and RabbitMQ with Docker
echo "🐳 Starting Redis and RabbitMQ containers..."
docker-compose -f docker-compose.minimal.yml up -d

echo ""
echo "⏳ Waiting for containers to start (10 seconds)..."
sleep 10

# Check Docker containers
echo ""
echo "🔍 Verifying Docker containers..."
if docker ps | grep -q niyanta_redis; then
    echo "✅ Redis container running"
else
    echo "❌ Redis container failed to start"
fi

if docker ps | grep -q niyanta_rabbitmq; then
    echo "✅ RabbitMQ container running"
else
    echo "❌ RabbitMQ container failed to start"
fi

echo ""
echo "📦 Installing Neo4j natively..."
echo ""

# Install Neo4j based on OS
if [ "$OS_TYPE" = "macOS" ]; then
    if command -v neo4j &> /dev/null; then
        echo "✅ Neo4j already installed"
    else
        brew install neo4j
    fi
    
    echo "🚀 Starting Neo4j..."
    brew services start neo4j
    
elif [ "$OS_TYPE" = "Linux" ]; then
    if command -v neo4j &> /dev/null; then
        echo "✅ Neo4j already installed"
    else
        # Add Neo4j repository
        wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
        echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
        sudo apt update
        sudo apt install neo4j -y
    fi
    
    echo "🚀 Starting Neo4j..."
    sudo systemctl start neo4j
    sudo systemctl enable neo4j
fi

echo ""
echo "⏳ Waiting for Neo4j to start (20 seconds)..."
sleep 20

echo ""
echo "🔍 Verifying all services..."
echo ""

# Test Redis
if docker exec niyanta_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running (Docker, port 6379)"
else
    echo "⚠️  Redis may not be ready yet"
fi

# Test RabbitMQ
if curl -s http://localhost:15672 > /dev/null 2>&1; then
    echo "✅ RabbitMQ is running (Docker, port 5672, UI: 15672)"
else
    echo "⚠️  RabbitMQ may not be ready yet"
fi

# Test Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j is running (Native, bolt: 7687, HTTP: 7474)"
else
    echo "⚠️  Neo4j may not be ready yet"
fi

echo ""
echo "=========================================================="
echo "✅ Hybrid Setup Complete!"
echo ""
echo "📝 What's running where:"
echo "   🐳 Docker: Redis + RabbitMQ (docker-compose.minimal.yml)"
echo "   💻 Native: Neo4j (system service)"
echo ""
echo "📝 Next Steps:"
echo "1. Configure Neo4j password:"
echo "   - Visit: http://localhost:7474"
echo "   - Login: neo4j/neo4j"
echo "   - Change password to: password"
echo ""
echo "2. Create .env file:"
echo "   cp .env.example .env"
echo ""
echo "3. Add your Groq API key to .env:"
echo "   GROQ_API_KEY=gsk_your_key_here"
echo ""
echo "4. Install Python dependencies:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Run the system:"
echo "   Terminal 1: python main.py"
echo "   Terminal 2: python worker_main.py"
echo ""
echo "🛠️  Management commands:"
echo "   Stop containers: docker-compose -f docker-compose.minimal.yml down"
echo "   Start containers: docker-compose -f docker-compose.minimal.yml up -d"
echo "   View logs: docker-compose -f docker-compose.minimal.yml logs -f"
echo ""
if [ "$OS_TYPE" = "macOS" ]; then
    echo "   Stop Neo4j: brew services stop neo4j"
    echo "   Start Neo4j: brew services start neo4j"
else
    echo "   Stop Neo4j: sudo systemctl stop neo4j"
    echo "   Start Neo4j: sudo systemctl start neo4j"
fi
echo ""
echo "🎉 Happy coding!"
