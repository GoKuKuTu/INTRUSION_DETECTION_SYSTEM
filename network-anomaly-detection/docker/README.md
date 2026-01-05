# Docker

## Build
```bash
# from repository root
docker compose -f docker/docker-compose.yml build
```

## Run
```bash
# from repository root
docker compose -f docker/docker-compose.yml up -d

# visit
# http://localhost:8000
```

## Logs
```bash
# follow logs
docker compose -f docker/docker-compose.yml logs -f app
```
