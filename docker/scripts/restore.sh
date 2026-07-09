#!/bin/bash

# ==========================================
# Restore Script
# ==========================================
# Restore from backup (optional services handled gracefully)

set -e

BACKUP_DIR="../backups"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}♻️  Niyanta Restore Script${NC}"
echo "=========================="
echo ""

# List available backups
echo "📦 Available backups:"
ls -lh "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || {
    echo -e "${RED}❌ No backups found${NC}"
    exit 1
}

echo ""
read -p "Enter backup filename (e.g., backup_20260310_120000.tar.gz): " BACKUP_FILE

if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found${NC}"
    exit 1
fi

echo ""
echo -e "${RED}⚠️  WARNING: This will stop all services and restore data${NC}"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
EXTRACT_DIR=$(basename "$BACKUP_FILE" .tar.gz)
echo ""
echo "📦 Extracting backup..."
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"

# Stop services
echo "🛑 Stopping services..."
cd ../
docker-compose -f ./docker-compose.yml down

# Restore Redis (REQUIRED)
echo "  ├─ Restoring Redis..."
if ! docker-compose -f ./docker-compose.yml up -d redis; then
    echo -e "${RED}    ❌ Failed to start Redis${NC}"
    exit 1
fi
sleep 5
if ! cat "$BACKUP_DIR/$EXTRACT_DIR/redis.rdb" | docker-compose -f ./docker-compose.yml exec -T redis redis-cli --pipe 2>/dev/null; then
    echo -e "${RED}    ❌ Failed to restore Redis data${NC}"
    exit 1
fi
echo "    ✓ Redis restored"

# Restore RabbitMQ (REQUIRED)
echo "  ├─ Restoring RabbitMQ..."
if ! docker-compose -f ./docker-compose.yml up -d rabbitmq; then
    echo -e "${RED}    ❌ Failed to start RabbitMQ${NC}"
    exit 1
fi
sleep 5
if [ -f "$BACKUP_DIR/$EXTRACT_DIR/rabbitmq.json" ]; then
    if curl -s -u guest:guest -X POST http://localhost:15672/api/definitions -H "Content-Type: application/json" -d @"$BACKUP_DIR/$EXTRACT_DIR/rabbitmq.json" >/dev/null 2>&1; then
        echo "    ✓ RabbitMQ restored"
    else
        echo -e "${YELLOW}    ⚠️  RabbitMQ restore failed (definitions not restored, but service running)${NC}"
    fi
else
    echo -e "${YELLOW}    ⚠️  RabbitMQ definitions not in backup${NC}"
fi

# Restore Neo4j (OPTIONAL)
if [ -f "$BACKUP_DIR/$EXTRACT_DIR/neo4j.dump" ]; then
    echo "  ├─ Restoring Neo4j..."
    if docker-compose -f ./docker-compose.yml up -d neo4j 2>/dev/null; then
        sleep 10
        if cat "$BACKUP_DIR/$EXTRACT_DIR/neo4j.dump" | docker-compose -f ./docker-compose.yml exec -T neo4j neo4j-admin database load --from-stdin neo4j --overwrite-destination=true 2>/dev/null; then
            echo "    ✓ Neo4j restored"
        else
            echo -e "${YELLOW}    ⚠️  Neo4j restore failed (optional service)${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  Neo4j not available (optional service)${NC}"
    fi
else
    echo "  ├─ Skipping Neo4j (not in backup)"
fi

# Restore ChromaDB (OPTIONAL)
if [ -d "$BACKUP_DIR/$EXTRACT_DIR/chromadb" ]; then
    echo "  ├─ Restoring ChromaDB..."
    if docker-compose -f ./docker-compose.yml up -d chromadb 2>/dev/null; then
        sleep 5
        if docker cp "$BACKUP_DIR/$EXTRACT_DIR/chromadb" niyanta_chromadb:/chroma/ >/dev/null 2>&1; then
            echo "    ✓ ChromaDB restored"
        else
            echo -e "${YELLOW}    ⚠️  ChromaDB restore failed (optional service)${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  ChromaDB not available (optional service)${NC}"
    fi
else
    echo "  ├─ Skipping ChromaDB (not in backup)"
fi

# Cleanup
rm -rf "$BACKUP_DIR/$EXTRACT_DIR"

# Restart all services
echo "  └─ Restarting all services..."
docker-compose -f ./docker-compose.yml up -d

echo ""
echo -e "${GREEN}✅ Restore completed successfully${NC}"
echo ""
echo "📊 Current services:"
docker-compose -f ./docker-compose.yml ps
