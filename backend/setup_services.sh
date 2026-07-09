#!/bin/bash

# Setup script for Agentic RAG System (macOS/Linux)
# Installs and starts Redis, RabbitMQ, and Neo4j

set -e

echo "🚀 Agentic RAG System - Service Setup"
echo "======================================"
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============= macOS Installation =============
if [ "$OS_TYPE" = "macOS" ]; then
    echo "🍺 Installing via Homebrew..."
    echo ""
    
    # Check if Homebrew is installed
    if ! command_exists brew; then
        echo "❌ Homebrew not found. Please install it first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "📦 Installing Redis..."
    if command_exists redis-server; then
        echo "✅ Redis already installed"
    else
        brew install redis
    fi
    
    echo ""
    echo "📦 Installing RabbitMQ..."
    if command_exists rabbitmq-server; then
        echo "✅ RabbitMQ already installed"
    else
        brew install rabbitmq
    fi
    
    echo ""
    echo "📦 Installing Neo4j..."
    if command_exists neo4j; then
        echo "✅ Neo4j already installed"
    else
        brew install neo4j
    fi
    
    echo ""
    echo "🚀 Starting services..."
    echo ""
    
    brew services start redis
    echo "✅ Redis started"
    
    brew services start rabbitmq
    echo "✅ RabbitMQ started"
    
    brew services start neo4j
    echo "✅ Neo4j started"
    
# ============= Linux Installation =============
elif [ "$OS_TYPE" = "Linux" ]; then
    echo "🐧 Installing via apt (Ubuntu/Debian)..."
    echo ""
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️  This script needs sudo privileges. You may be prompted for your password."
        echo ""
    fi
    
    sudo apt update
    
    echo "📦 Installing Redis..."
    if command_exists redis-server; then
        echo "✅ Redis already installed"
    else
        sudo apt install redis-server -y
    fi
    
    echo ""
    echo "📦 Installing RabbitMQ..."
    if command_exists rabbitmq-server; then
        echo "✅ RabbitMQ already installed"
    else
        sudo apt install rabbitmq-server -y
    fi
    
    echo ""
    echo "📦 Installing Neo4j..."
    if command_exists neo4j; then
        echo "✅ Neo4j already installed"
    else
        # Add Neo4j repository
        wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
        echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
        sudo apt update
        sudo apt install neo4j -y
    fi
    
    echo ""
    echo "🚀 Starting services..."
    echo ""
    
    sudo systemctl start redis
    sudo systemctl enable redis
    echo "✅ Redis started"
    
    sudo systemctl start rabbitmq-server
    sudo systemctl enable rabbitmq-server
    sudo rabbitmq-plugins enable rabbitmq_management
    echo "✅ RabbitMQ started"
    
    sudo systemctl start neo4j
    sudo systemctl enable neo4j
    echo "✅ Neo4j started"
    
else
    echo "❌ Unsupported OS: $OS_TYPE"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "🔍 Verifying services..."
echo ""

# Test Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running (port 6379)"
else
    echo "⚠️  Redis may not be ready yet. Try: redis-cli ping"
fi

# Test RabbitMQ
if curl -s http://localhost:15672 > /dev/null 2>&1; then
    echo "✅ RabbitMQ is running (port 5672, management UI: 15672)"
else
    echo "⚠️  RabbitMQ may not be ready yet. Try: curl http://localhost:15672"
fi

# Test Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j is running (bolt: 7687, HTTP: 7474)"
else
    echo "⚠️  Neo4j may not be ready yet. Try: curl http://localhost:7474"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Create .env file:"
echo "   cp .env.example .env"
echo ""
echo "2. Add your Groq API key to .env:"
echo "   GROQ_API_KEY=gsk_your_key_here"
echo ""
echo "3. Set Neo4j password (first login):"
echo "   - Visit: http://localhost:7474"
echo "   - Login: neo4j/neo4j"
echo "   - Change password to: password"
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
echo "🎉 Happy coding!"
