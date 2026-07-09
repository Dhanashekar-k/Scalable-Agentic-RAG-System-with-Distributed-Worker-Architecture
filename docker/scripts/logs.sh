#!/bin/bash

# ==========================================
# View Logs Script
# ==========================================
# Easy access to container logs
# Usage: ./logs.sh (run from docker/ directory)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📋 Niyanta Logs Viewer${NC}"
echo "======================"
echo ""
echo "Available services:"
echo "  1) All services"
echo "  2) Backend only"
echo "  3) Workers (all - scalable)"
echo "  4) Redis"
echo "  5) RabbitMQ"
echo ""
read -p "Select service (1-5): " choice

case $choice in
    1)
        docker-compose logs -f
        ;;
    2)
        docker-compose logs -f backend
        ;;
    3)
        docker-compose logs -f worker
        ;;
    4)
        docker-compose logs -f redis
        ;;
    5)
        docker-compose logs -f rabbitmq
        ;;
    *)
        echo -e "${YELLOW}Invalid choice${NC}"
        exit 1
        ;;
esac
