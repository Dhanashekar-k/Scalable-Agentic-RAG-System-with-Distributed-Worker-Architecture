#!/bin/bash

# ==========================================
# Backup Script
# ==========================================
# Backup all database volumes (optional services handled gracefully)

set -e

BACKUP_DIR="../backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}💾 Niyanta Backup Script${NC}"
echo "========================"

# Create backup directory
mkdir -p "$BACKUP_PATH"

echo ""
echo "📦 Creating backup at: $BACKUP_PATH"

# Backup Redis (REQUIRED)
echo "  ├─ Backing up Redis..."
if ! docker-compose -f ./docker-compose.yml exec -T redis redis-cli --rdb - > "$BACKUP_PATH/redis.rdb" 2>/dev/null; then
    echo -e "${RED}    ❌ Failed to backup Redis${NC}"
    exit 1
fi

# Backup RabbitMQ (REQUIRED)
echo "  ├─ Backing up RabbitMQ..."
if ! curl -s -u guest:guest http://localhost:15672/api/definitions -o "$BACKUP_PATH/rabbitmq.json" 2>/dev/null; then
    echo -e "${RED}    ❌ Failed to backup RabbitMQ${NC}"
    exit 1
fi

# Backup Neo4j (OPTIONAL)
if docker-compose -f ./docker-compose.yml ps | grep -q "neo4j" 2>/dev/null; then
    echo "  ├─ Backing up Neo4j..."
    if docker-compose -f ./docker-compose.yml exec -T neo4j neo4j-admin database dump neo4j --to-stdout > "$BACKUP_PATH/neo4j.dump" 2>/dev/null; then
        echo "    ✓ Neo4j backed up"
    else
        echo -e "${YELLOW}    ⚠️  Neo4j backup failed (optional service)${NC}"
    fi
else
    echo "  ├─ Skipping Neo4j (not running)"
fi

# Backup ChromaDB (OPTIONAL)
if docker-compose -f ./docker-compose.yml ps | grep -q "chromadb" 2>/dev/null; then
    echo "  ├─ Backing up ChromaDB..."
    if docker cp niyanta_chromadb:/chroma/chroma "$BACKUP_PATH/chromadb" >/dev/null 2>&1; then
        echo "    ✓ ChromaDB backed up"
    else
        echo -e "${YELLOW}    ⚠️  ChromaDB backup failed (optional service)${NC}"
    fi
else
    echo "  ├─ Skipping ChromaDB (not running)"
fi

# Compress backup
echo "  └─ Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "backup_$TIMESTAMP.tar.gz" "backup_$TIMESTAMP"
rm -rf "backup_$TIMESTAMP"

echo ""
echo -e "${GREEN}✅ Backup completed: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz${NC}"

# Keep only last 7 backups
echo "🧹 Cleaning old backups (keeping last 7)..."
ls -t backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo ""
echo "📊 Available backups:"
ls -lh backup_*.tar.gz 2>/dev/null || echo "  No backups found"
