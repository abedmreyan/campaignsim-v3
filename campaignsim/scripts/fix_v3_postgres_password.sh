#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env.production"
DB_URL=$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)
PG_PASSWORD=$(echo "$DB_URL" | sed -E 's#postgresql://[^:]+:([^@]+)@.*#\1#')
GATEWAY_IP=$(echo "$DB_URL" | sed -E 's#.*@([0-9.]+):.*#\1#')

echo "Password length being applied: ${#PG_PASSWORD} chars"

sudo -u postgres psql -p 5433 -v ON_ERROR_STOP=1 -c \
  "ALTER ROLE cs_v3_user WITH PASSWORD '${PG_PASSWORD}';"

echo "== Re-verifying from inside the Docker network =="
docker run --rm --network aether-hosting -e PGPASSWORD="$PG_PASSWORD" postgres:18-alpine \
  psql -h "$GATEWAY_IP" -p 5433 -U cs_v3_user -d campaignsim_v3 -c "SELECT 'v3 cluster reachable' AS status;"
