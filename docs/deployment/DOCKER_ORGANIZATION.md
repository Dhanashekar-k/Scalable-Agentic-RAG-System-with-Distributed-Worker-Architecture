# 🐳 Docker Files - Organized Structure

All Docker-related files have been organized into the `docker/` directory for better project structure.

## 📁 Directory Layout

```
Scalable RAG/
├── deploy.sh                        # ← Quick wrapper (calls docker/scripts/deploy.sh)
├── logs.sh                          # ← Quick wrapper (calls docker/scripts/logs.sh)
├── .env                             # ← Your environment config (create from docker/config/.env.example)
│
├── docker/                          # ← All Docker files here
│   ├── README.md                    # Docker documentation
│   ├── DOCKER_SETUP_SUMMARY.md      # What was created
│   ├── DOCKER_QUICK_REFERENCE.txt   # Command reference
│   │
│   ├── docker-compose.yml           # Production setup
│   ├── docker-compose.dev.yml       # Development overrides
│   │
│   ├── config/
│   │   └── .env.example            # Environment template
│   │
│   ├── scripts/
│   │   ├── deploy.sh               # Deployment automation
│   │   ├── logs.sh                 # Log viewer
│   │   ├── backup.sh               # Database backup
│   │   └── restore.sh              # Restore backup
│   │
│   └── nginx/
│       └── nginx.conf              # Reverse proxy config
│
├── backend/
│   ├── Dockerfile                   # Backend container
│   ├── Dockerfile.worker            # Worker container
│   └── .dockerignore
│
└── frontend/
    ├── Dockerfile                   # Frontend container
    └── .dockerignore
```

## 🚀 Quick Start

```bash
# 1. Configure environment
cp docker/config/.env.example .env
nano .env  # Add your GROQ_API_KEY

# 2. Deploy (use convenience wrapper in root)
./deploy.sh

# OR use full path
./docker/scripts/deploy.sh
```

## 📖 Documentation

- **[docker/README.md](docker/README.md)** - Docker documentation
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Full deployment guide

## 🛠️ Common Commands

All commands work from project root:

```bash
# Using convenience wrappers (recommended)
./deploy.sh                # Deploy everything
./logs.sh                  # View logs

# Using full paths
./docker/scripts/deploy.sh
./docker/scripts/logs.sh
./docker/scripts/backup.sh
./docker/scripts/restore.sh

# Using docker-compose directly
docker-compose -f docker/docker-compose.yml ps
docker-compose -f docker/docker-compose.yml logs -f
docker-compose -f docker/docker-compose.yml restart
docker-compose -f docker/docker-compose.yml down
```

## ✨ What Changed?

### Before (Files scattered)
```
Scalable RAG/
├── deploy.sh
├── logs.sh
├── backup.sh
├── restore.sh
├── .env.example
├── docker-compose.yml
├── docker-compose.dev.yml
├── DOCKER_SETUP_SUMMARY.md
├── DOCKER_QUICK_REFERENCE.txt
└── nginx/
    └── nginx.conf
```

### After (Organized)
```
Scalable RAG/
├── deploy.sh (wrapper) ───┐
├── logs.sh (wrapper) ─────┤
├── .env                   │
└── docker/                │
    ├── README.md          │
    ├── docker-compose.yml │
    ├── config/            │
    ├── scripts/ ◄─────────┘ All Docker files here
    └── nginx/
```

## 🎯 Benefits

✅ **Cleaner root directory** - Less clutter
✅ **Better organization** - All Docker files in one place
✅ **Easy to find** - Everything Docker-related is in `docker/`
✅ **Still convenient** - Wrapper scripts in root for quick access
✅ **Portable** - Copy `docker/` folder to deploy anywhere

## 🔄 Migration Notes

If you had the old structure:

1. ✅ All files moved to `docker/` directory
2. ✅ Scripts updated with new paths
3. ✅ Documentation updated
4. ✅ Convenience wrappers created in root
5. ✅ Everything still works the same way!

**Nothing breaks - you can still use `./deploy.sh` from root!**
