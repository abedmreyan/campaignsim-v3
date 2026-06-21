#!/bin/bash
# =============================================================================
# CampaignSim — Automated Server Setup
# Tested on: Ubuntu 24.04 LTS
# Usage: bash setup.sh
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info()  { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo -e "${BLUE}=================================================="
echo "   CampaignSim Server Setup"
echo -e "==================================================${NC}"
echo ""

# =============================================================================
# CONFIGURATION
# =============================================================================
DOMAIN="campaignsim-gv4.aethersystems.co"
REPO="abedmreyan/campaignsim-v3"
APP_DIR="/opt/campaignsim"
DB_NAME="campaignsim"
DB_USER="campaignsim"
DB_PASS=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 24)

echo -e "${YELLOW}Enter your GitHub personal access token:${NC}"
read -rs GITHUB_TOKEN
echo ""

echo -e "${YELLOW}Enter your DeepSeek API key (LLM_API_KEY):${NC}"
read -rs LLM_API_KEY
echo ""

[ -z "$GITHUB_TOKEN" ] && error "GitHub token is required"
[ -z "$LLM_API_KEY" ]  && error "LLM API key is required"

echo ""
log "Setting up CampaignSim on: $DOMAIN"
echo ""

# =============================================================================
# PHASE 1 — System packages
# =============================================================================
log "Updating system packages..."
sudo apt-get update -y -q
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q

log "Installing system dependencies..."
sudo apt-get install -y -q \
  git curl wget gnupg ca-certificates software-properties-common \
  build-essential pkg-config \
  libpq-dev libffi-dev libssl-dev \
  libmupdf-dev mupdf-tools \
  libblas-dev liblapack-dev gfortran \
  nginx \
  postgresql postgresql-contrib \
  openssl

# =============================================================================
# PHASE 2 — Python 3.12
# =============================================================================
log "Ensuring Python 3.12 is installed..."

# Ubuntu 24.04 ships with 3.12; add deadsnakes PPA as fallback for older systems
if ! python3.12 --version &>/dev/null; then
  warn "Python 3.12 not found — installing via deadsnakes PPA..."
  sudo add-apt-repository ppa:deadsnakes/ppa -y
  sudo apt-get update -q
  sudo apt-get install -y -q python3.12 python3.12-venv python3.12-dev
else
  sudo apt-get install -y -q python3.12-venv python3.12-dev
fi

PYTHON=$(which python3.12)
log "Using Python: $($PYTHON --version)"

# =============================================================================
# PHASE 3 — Node.js 20
# =============================================================================
log "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
sudo apt-get install -y -q nodejs
log "Using Node: $(node --version), npm: $(npm --version)"

# =============================================================================
# PHASE 4 — cloudflared
# =============================================================================
log "Installing cloudflared..."
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg 2>/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list > /dev/null
sudo apt-get update -q && sudo apt-get install -y -q cloudflared

# =============================================================================
# PHASE 5 — PostgreSQL
# =============================================================================
log "Setting up PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" 2>/dev/null \
  || warn "DB user already exists — skipping"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null \
  || warn "Database already exists — skipping"

# =============================================================================
# PHASE 6 — Clone repository
# =============================================================================
log "Cloning repository..."
sudo mkdir -p ${APP_DIR}
sudo chown $USER:$USER ${APP_DIR}

if [ -d "${APP_DIR}/.git" ]; then
  warn "Repo already present — pulling latest..."
  cd ${APP_DIR} && git pull
else
  git clone "https://${GITHUB_TOKEN}@github.com/${REPO}.git" ${APP_DIR}
  cd ${APP_DIR} && git checkout deploy/stable
fi

# =============================================================================
# PHASE 7 — Environment file
# =============================================================================
log "Writing .env file..."
cat > ${APP_DIR}/campaignsim/.env << EOF
LLM_API_KEY=${LLM_API_KEY}
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-chat
KG_BACKEND=local
SECRET_KEY=${SECRET_KEY}
FLASK_DEBUG=False
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
POSTGRES_PASSWORD=${DB_PASS}
JWT_SECRET=${JWT_SECRET}
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=30
EOF

# =============================================================================
# PHASE 8 — Python backend
# =============================================================================
log "Creating Python 3.12 virtual environment..."
cd ${APP_DIR}/campaignsim/backend
$PYTHON -m venv .venv

log "Upgrading pip..."
.venv/bin/pip install --upgrade pip setuptools wheel -q

log "Installing Python dependencies (this takes 5-10 minutes due to camel-ai/oasis)..."
.venv/bin/pip install \
  --timeout 120 \
  --retries 5 \
  -r requirements.txt

# Fix missing Text import in migration if not already present
MIGRATION_FILE="${APP_DIR}/campaignsim/backend/migrations/versions/26473512e1aa_initial_schema_users_refresh_tokens_.py"
if [ -f "$MIGRATION_FILE" ] && ! grep -q "from sqlalchemy import Text" "$MIGRATION_FILE"; then
  sed -i '/^from alembic import op/a from sqlalchemy import Text' "$MIGRATION_FILE"
  log "Fixed migration file (added missing Text import)"
fi

log "Running database migrations..."
FLASK_APP=app .venv/bin/flask db upgrade

# =============================================================================
# PHASE 9 — Frontend build
# =============================================================================
log "Installing frontend dependencies..."
cd ${APP_DIR}/campaignsim-v3/frontend
npm install --silent

log "Building frontend..."
npm run build

# =============================================================================
# PHASE 10 — Nginx
# =============================================================================
log "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/campaignsim > /dev/null << NGINX
server {
    listen 80;
    server_name ${DOMAIN};

    root ${APP_DIR}/campaignsim-v3/frontend/dist;
    index index.html;

    # Vue Router — all non-file paths serve index.html
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to Flask
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        client_max_body_size 50M;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/campaignsim /etc/nginx/sites-enabled/campaignsim
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl enable nginx && sudo systemctl restart nginx

# =============================================================================
# PHASE 11 — Flask systemd service
# =============================================================================
log "Creating Flask systemd service..."
sudo tee /etc/systemd/system/campaignsim.service > /dev/null << SERVICE
[Unit]
Description=CampaignSim Flask Backend
After=network.target postgresql.service

[Service]
User=${USER}
WorkingDirectory=${APP_DIR}/campaignsim/backend
Environment=PATH=${APP_DIR}/campaignsim/backend/.venv/bin
ExecStart=${APP_DIR}/campaignsim/backend/.venv/bin/python run.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable campaignsim
sudo systemctl start campaignsim

sleep 4
if sudo systemctl is-active --quiet campaignsim; then
  log "Flask backend is running"
else
  error "Flask backend failed to start. Run: sudo journalctl -u campaignsim -n 50"
fi

# =============================================================================
# PHASE 12 — Cloudflare Tunnel
# =============================================================================
echo ""
echo -e "${BLUE}=================================================="
echo "   Cloudflare Tunnel Setup"
echo -e "==================================================${NC}"
echo ""
info "A browser window will open for Cloudflare authentication."
info "Log in with the account that manages aethersystems.co"
echo ""
read -p "Press ENTER to open Cloudflare login..."

cloudflared tunnel login

log "Creating tunnel..."
cloudflared tunnel create campaignsim-home 2>/dev/null || warn "Tunnel already exists"

TUNNEL_ID=$(cloudflared tunnel list 2>/dev/null | grep "campaignsim-home" | awk '{print $1}')
[ -z "$TUNNEL_ID" ] && error "Could not get tunnel ID. Run: cloudflared tunnel list"

log "Tunnel ID: $TUNNEL_ID"

mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ${DOMAIN}
    service: http://localhost:80
  - service: http_status:404
EOF

log "Creating DNS record in Cloudflare..."
cloudflared tunnel route dns campaignsim-home ${DOMAIN}

log "Installing tunnel as system service..."
sudo tee /etc/systemd/system/cloudflared.service > /dev/null << SERVICE
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
User=${USER}
ExecStart=/usr/bin/cloudflared tunnel --config ${HOME}/.cloudflared/config.yml run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

sleep 3
if sudo systemctl is-active --quiet cloudflared; then
  log "Cloudflare Tunnel is running"
else
  warn "Tunnel may still be starting. Check: sudo journalctl -u cloudflared -n 30"
fi

# =============================================================================
# COMPLETE
# =============================================================================
echo ""
echo -e "${GREEN}=================================================="
echo "   Setup Complete!"
echo -e "==================================================${NC}"
echo ""
echo -e "  App URL:    ${BLUE}https://${DOMAIN}${NC}"
echo ""
echo -e "  Flask:      $(sudo systemctl is-active campaignsim)"
echo -e "  Nginx:      $(sudo systemctl is-active nginx)"
echo -e "  Tunnel:     $(sudo systemctl is-active cloudflared)"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View Flask logs:   sudo journalctl -u campaignsim -f"
echo "  View tunnel logs:  sudo journalctl -u cloudflared -f"
echo "  Restart app:       sudo systemctl restart campaignsim"
echo "  Update app:        cd ${APP_DIR} && git pull && sudo systemctl restart campaignsim"
echo ""
