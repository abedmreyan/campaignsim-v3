#!/bin/bash
# =============================================================================
# CampaignSim v5 — Linux Setup (Ubuntu 22.04 / 24.04)
# Usage: bash setup-linux.sh
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }
info()  { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo -e "${BLUE}=================================================="
echo "   CampaignSim v5 — Linux Setup"
echo -e "==================================================${NC}"
echo ""

# =============================================================================
# CONFIGURATION — prompts
# =============================================================================
REPO="abedmreyan/campaignsim-v3"
BRANCH="v5"
APP_DIR="/opt/campaignsim"
DB_NAME="campaignsim"
DB_USER="campaignsim"
DB_PASS=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 24)

echo -e "${YELLOW}Enter your domain (e.g. campaignsim.example.com):${NC}"
read -r DOMAIN
[ -z "$DOMAIN" ] && error "Domain is required"

echo -e "${YELLOW}Enter your GitHub personal access token:${NC}"
read -rs GITHUB_TOKEN
echo ""
[ -z "$GITHUB_TOKEN" ] && error "GitHub token is required"

echo -e "${YELLOW}Enter your LLM API key (DeepSeek or OpenAI):${NC}"
read -rs LLM_API_KEY
echo ""
[ -z "$LLM_API_KEY" ] && error "LLM API key is required"

echo -e "${YELLOW}Enter your LLM base URL [https://api.deepseek.com]:${NC}"
read -r LLM_BASE_URL
LLM_BASE_URL="${LLM_BASE_URL:-https://api.deepseek.com}"

echo -e "${YELLOW}Enter your LLM model name [deepseek-chat]:${NC}"
read -r LLM_MODEL_NAME
LLM_MODEL_NAME="${LLM_MODEL_NAME:-deepseek-chat}"

echo ""
log "Deploying CampaignSim v5 on: ${DOMAIN}"
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
# PHASE 2 — Python 3.11
# =============================================================================
log "Ensuring Python 3.11 is installed..."
# camel-oasis==0.2.5 requires Python >=3.10,<3.12

if ! python3.11 --version &>/dev/null; then
  warn "Python 3.11 not found — installing via deadsnakes PPA..."
  sudo add-apt-repository ppa:deadsnakes/ppa -y
  sudo apt-get update -q
  sudo apt-get install -y -q python3.11 python3.11-venv python3.11-dev
else
  sudo apt-get install -y -q python3.11-venv python3.11-dev
fi

PYTHON=$(which python3.11)
log "Using Python: $($PYTHON --version)"

# =============================================================================
# PHASE 3 — Node.js 20
# =============================================================================
log "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
sudo apt-get install -y -q nodejs
log "Node: $(node --version)  npm: $(npm --version)"

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
  || warn "DB user already exists — reusing"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null \
  || warn "Database already exists — reusing"

# =============================================================================
# PHASE 6 — Clone repository (v5 branch)
# =============================================================================
log "Cloning CampaignSim v5..."
sudo mkdir -p ${APP_DIR}
sudo chown $USER:$USER ${APP_DIR}

if [ -d "${APP_DIR}/.git" ]; then
  warn "Repo already present — pulling latest ${BRANCH}..."
  cd ${APP_DIR}
  git fetch origin
  git checkout ${BRANCH}
  git pull origin ${BRANCH}
else
  git clone --branch ${BRANCH} "https://${GITHUB_TOKEN}@github.com/${REPO}.git" ${APP_DIR}
fi

# =============================================================================
# PHASE 7 — Environment file
# =============================================================================
log "Writing .env file..."
cat > ${APP_DIR}/campaignsim/.env << EOF
# CampaignSim v5 — generated by setup-linux.sh
LLM_API_KEY=${LLM_API_KEY}
LLM_BASE_URL=${LLM_BASE_URL}
LLM_MODEL_NAME=${LLM_MODEL_NAME}
KG_BACKEND=local
SECRET_KEY=${SECRET_KEY}
FLASK_DEBUG=False
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
POSTGRES_PASSWORD=${DB_PASS}
JWT_SECRET=${JWT_SECRET}
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=30
EOF

log ".env written to ${APP_DIR}/campaignsim/.env"
info "Save these credentials somewhere safe:"
echo "  DB_PASS:    ${DB_PASS}"
echo "  JWT_SECRET: ${JWT_SECRET}"
echo "  SECRET_KEY: ${SECRET_KEY}"
echo ""

# =============================================================================
# PHASE 8 — Python virtual environment + dependencies
# =============================================================================
log "Creating Python 3.11 virtual environment..."
cd ${APP_DIR}/campaignsim/backend

if [ -d ".venv" ] && ! .venv/bin/python --version 2>&1 | grep -q "3.11"; then
  warn "Removing existing venv (wrong Python version)..."
  rm -rf .venv
fi

$PYTHON -m venv .venv
.venv/bin/pip install --upgrade pip setuptools wheel -q

log "Installing Python dependencies (5-10 min due to torch/camel-ai)..."
.venv/bin/pip install \
  --timeout 120 \
  --retries 5 \
  -r requirements.txt

# Fix missing Text import in migration (safe to run multiple times)
MIGRATION_FILE="${APP_DIR}/campaignsim/backend/migrations/versions/26473512e1aa_initial_schema_users_refresh_tokens_.py"
if [ -f "$MIGRATION_FILE" ] && ! grep -q "from sqlalchemy import Text" "$MIGRATION_FILE"; then
  sed -i '/^from alembic import op/a from sqlalchemy import Text' "$MIGRATION_FILE"
  log "Fixed migration file (Text import)"
fi

log "Running database migrations..."
FLASK_APP=app .venv/bin/flask db upgrade

# =============================================================================
# PHASE 9 — Frontend (pre-built dist is in v5 branch — no rebuild needed)
# =============================================================================
log "Frontend dist is pre-built in v5 branch — skipping npm build"
info "Dist located at: ${APP_DIR}/campaignsim-v3/frontend/dist"

# =============================================================================
# PHASE 10 — Nginx
# =============================================================================
log "Configuring Nginx for ${DOMAIN}..."
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

    # Proxy API calls to Flask
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
log "Nginx configured and running"

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
info "Log in with the Cloudflare account that manages your domain."
echo ""
read -p "Press ENTER to open Cloudflare login..."

cloudflared tunnel login

TUNNEL_NAME="campaignsim-$(echo ${DOMAIN} | tr '.' '-')"
log "Creating tunnel: ${TUNNEL_NAME}..."
cloudflared tunnel create ${TUNNEL_NAME} 2>/dev/null || warn "Tunnel already exists"

TUNNEL_ID=$(cloudflared tunnel list 2>/dev/null | grep "${TUNNEL_NAME}" | awk '{print $1}')
[ -z "$TUNNEL_ID" ] && error "Could not get tunnel ID. Run: cloudflared tunnel list"

log "Tunnel ID: ${TUNNEL_ID}"

mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ${DOMAIN}
    service: http://localhost:80
  - service: http_status:404
EOF

log "Creating DNS CNAME for ${DOMAIN}..."
cloudflared tunnel route dns ${TUNNEL_NAME} ${DOMAIN}

log "Installing cloudflared as systemd service..."
sudo tee /etc/systemd/system/cloudflared.service > /dev/null << SERVICE
[Unit]
Description=Cloudflare Tunnel — CampaignSim
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
  log "Cloudflare Tunnel running"
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
echo -e "  PostgreSQL: $(sudo systemctl is-active postgresql)"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  Logs (Flask):    sudo journalctl -u campaignsim -f"
echo "  Logs (tunnel):   sudo journalctl -u cloudflared -f"
echo "  Restart Flask:   sudo systemctl restart campaignsim"
echo "  Update to latest:"
echo "    cd ${APP_DIR} && git pull origin ${BRANCH} && sudo systemctl restart campaignsim"
echo ""
