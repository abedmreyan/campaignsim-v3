#!/usr/bin/env bash
# One-time setup: new, independent Postgres cluster for the campaignsim-v3
# staging/production instance. Does NOT touch the existing "main" cluster
# (port 5432, backing /opt/campaignsim) in any way.
set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env.production"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

DB_URL=$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)
PG_PASSWORD=$(echo "$DB_URL" | sed -E 's#postgresql://[^:]+:([^@]+)@.*#\1#')
GATEWAY_IP=$(echo "$DB_URL" | sed -E 's#.*@([0-9.]+):.*#\1#')

if [ -z "$PG_PASSWORD" ] || [ -z "$GATEWAY_IP" ]; then
  echo "Failed to parse DATABASE_URL from $ENV_FILE" >&2
  exit 1
fi

echo "== Creating new cluster 'campaignsim_v3' on port 5433 =="
sudo pg_createcluster 18 campaignsim_v3 -p 5433
sudo systemctl enable --now postgresql@18-campaignsim_v3

CONF_DIR="/etc/postgresql/18/campaignsim_v3"

echo "== Configuring listen_addresses (new cluster only) =="
sudo sed -i "s/^#\?listen_addresses.*/listen_addresses = 'localhost,${GATEWAY_IP}'/" "${CONF_DIR}/postgresql.conf"

echo "== Adding pg_hba.conf rule for the aether-hosting bridge (new cluster only) =="
echo "host    campaignsim_v3    cs_v3_user    172.19.0.0/16    scram-sha-256" | sudo tee -a "${CONF_DIR}/pg_hba.conf" > /dev/null

echo "== Restarting ONLY the new cluster =="
sudo systemctl restart postgresql@18-campaignsim_v3

echo "== Creating role + database =="
sudo -u postgres psql -p 5433 -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cs_v3_user') THEN
    CREATE ROLE cs_v3_user WITH LOGIN PASSWORD '${PG_PASSWORD}';
  END IF;
END
\$\$;
SQL
sudo -u postgres psql -p 5433 -tc "SELECT 1 FROM pg_database WHERE datname = 'campaignsim_v3'" | grep -q 1 || \
  sudo -u postgres psql -p 5433 -c "CREATE DATABASE campaignsim_v3 OWNER cs_v3_user;"

echo "== Verifying reachability from the Docker bridge gateway =="
PGPASSWORD="$PG_PASSWORD" psql -h "$GATEWAY_IP" -p 5433 -U cs_v3_user -d campaignsim_v3 -c "SELECT 'v3 cluster reachable' AS status;"

echo "== Confirming the EXISTING main cluster is untouched =="
sudo systemctl status postgresql --no-pager | head -5
pg_lsclusters

echo "Done."
