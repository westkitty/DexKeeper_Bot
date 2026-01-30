# DexKeeper Bot - Docker Deployment

## Quick Start

```bash
# 1. Create data directory
mkdir -p data

# 2. Build image
docker-compose build

# 3. Start bot
docker-compose up -d

# 4. View logs
docker-compose logs -f dexkeeper-bot
```

## Stop Bot

```bash
docker-compose down
```

## View Logs

```bash
docker-compose logs -f
```

## Update & Restart

```bash
docker-compose build --no-cache
docker-compose restart
```

## Backup Database

```bash
cp data/dexkeeper.db data/backup_$(date +%Y%m%d).db
```

---

