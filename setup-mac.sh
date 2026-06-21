#!/bin/bash
# =============================================================================
# CampaignSim v5 — macOS Setup (Homebrew)
# Usage: bash setup-mac.sh
# Tested on: macOS 14+ (Apple Silicon & Intel)
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
echo "   CampaignSim v5 — macOS Setup"
echo -e "==================================================${NC}"
echo ""

# =============================================================================
# CONFIGURATION — prompts
# =============================================================================
REPO="abedmreyan/campaignsim-v3"
BRANCH="v5"
APP_DIR="${HOME}/campaignsim"
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
log "App directory: ${APP_DIR}"
echo ""

# =============================================================================
# PHASE 1 — Homebrew
# =============================================================================
if ! command -v brew &>/dev/null; then
  log "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to PATH for Apple Silicon
  if [ -f "/opt/homebrew/bin/brew" ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  log "Homebrew already installed — updating..."
  brew update -q
fi

# =============================================================================
# PHASE 2 — System tools
# =============================================================================
log "Installing system tools..."
brew install git curl wget openssl 2>/dev/null || warn "Some tools already installed"

# =============================================================================
# PHASE 3 — Python 3.11
# =============================================================================
log "Installing Python 3.11..."
# camel-oasis==0.2.5 requires Python >=3.10,<3.12
brew install python@3.11 2>/dev/null || warn "Python 3.11 already installed"

# Resolve the python3.11 binary
if command -v python3.11 &>/dev/null; then
  PYTHON=$(command -v python3.11)
elif [ -f "/opt/homebrew/bin/python3.11" ]; then
  PYTHON="/opt/homebrew/bin/python3.11"
elif [ -f "/usr/local/bin/python3.11" ]; then
  PYTHON="/usr/local/bin/python3.11"
else
  error "python3.11 not found after install. Check: brew info python@3.11"
fi

log "Using Python: $($PYTHON --version) at ${PYTHON}"

# =============================================================================
# PHASE 4 — Node.js
# =============================================================================
log "Installing Node.js..."
brew install node@20 2>/dev/null || warn "Node already installed"
brew link --overwrite node@20 2>/dev/null || true
log "Node: $(node --version)  npm: $(npm --version)"

# =============================================================================
# PHASE 5 — PostgreSQL
# =============================================================================
log "Installing PostgreSQL..."
brew install postgresql@16 2>/dev/null || warn "PostgreSQL already installed"
brew link --overwrite postgresql@16 2>/dev/null || true

log "Starting PostgreSQL..."
brew services start postgresql@16

# Wait for Postgres to be ready
for i in {1..10}; do
  pg_isready -q 2>/dev/null && break
  warn "Waiting for PostgreSQL... ($i/10)"
  sleep 2
done
pg_isready -q || error "PostgreSQL failed to start"

log "Creating database user and database..."
createuser -s "${DB_USER}" 2>/dev/null || warn "DB user already exists — reusing"
createdb -O "${DB_USER}" "${DB_NAME}" 2>/dev/null || warn "Database already exists — reusing"
psql "${DB_NAME}" -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" 2>/dev/null || true

# =============================================================================
# PHASE 6 — Nginx
# =============================================================================
log "Installing Nginx..."
brew install nginx 2>/dev/null || warn "Nginx already installed"

# =============================================================================
# PHASE 7 — cloudflared
# =============================================================================
log "Installing cloudflared..."
brew install cloudflare/cloudflare/cloudflared 2>/dev/null || warn "cloudflared already installed"

# =============================================================================
# PHASE 8 — Clone repository (v5 branch)
# =============================================================================
log "Cloning CampaignSim v5..."
mkdir -p "${APP_DIR}"

if [ -d "${APP_DIR}/.git" ]; then
  warn "Repo already present — pulling latest ${BRANCH}..."
  cd "${APP_DIR}"
  git fetch origin
  git checkout "${BRANCH}"
  git pull origin "${BRANCH}"
else
  git clone --branch "${BRANCH}" "https://${GITHUB_TOKEN}@github.com/${REPO}.git" "${APP_DIR}"
fi

# =============================================================================
# PHASE 9 — Environment file
# =============================================================================
log "Writing .env file..."
cat > "${APP_DIR}/campaignsim/.env" << EOF
# CampaignSim v5 — generated by setup-mac.sh
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
info "Save these credentials:"
echo "  DB_PASS:    ${DB_PASS}"
echo "  JWT_SECRET: ${JWT_SECRET}"
echo "  SECRET_KEY: ${SECRET_KEY}"
echo ""

# =============================================================================
# PHASE 10 — Python virtual environment + dependencies
# =============================================================================
log "Creating Python 3.11 virtual environment..."
cd "${APP_DIR}/campaignsim/backend"

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
  # macOS sed requires empty string for -i
  sed -i '' '/^from alembic import op/a\
from sqlalchemy import Text' "$MIGRATION_FILE"
  log "Fixed migration file (Text import)"
fi

log "Running database migrations..."
FLASK_APP=app .venv/bin/flask db upgrade

# =============================================================================
# PHASE 11 — Frontend (pre-built dist is in v5 branch)
# =============================================================================
log "Frontend dist is pre-built in v5 — skipping npm build"
info "Dist: ${APP_DIR}/campaignsim-v3/frontend/dist"

# =============================================================================
# PHASE 12 — Nginx configuration
# =============================================================================
log "Configuring Nginx for ${DOMAIN}..."

# Find nginx config directory (Homebrew location varies by arch)
if [ -d "/opt/homebrew/etc/nginx" ]; then
  NGINX_CONF_DIR="/opt/homebrew/etc/nginx"
elif [ -d "/usr/local/etc/nginx" ]; then
  NGINX_CONF_DIR="/usr/local/etc/nginx"
else
  error "Could not find Nginx config directory"
fi

mkdir -p "${NGINX_CONF_DIR}/servers"

cat > "${NGINX_CONF_DIR}/servers/campaignsim.conf" << NGINX
server {
    listen 80;
    server_name ${DOMAIN};

    root ${APP_DIR}/campaignsim-v3/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

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

nginx -t && brew services restart nginx
log "Nginx configured and running"

# =============================================================================
# PHASE 13 — Flask as a launchd service
# =============================================================================
log "Creating Flask launchd service..."
PLIST_PATH="${HOME}/Library/LaunchAgents/co.campaignsim.flask.plist"

cat > "${PLIST_PATH}" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>co.campaignsim.flask</string>
    <key>ProgramArguments</key>
    <array>
        <string>${APP_DIR}/campaignsim/backend/.venv/bin/python</string>
        <string>${APP_DIR}/campaignsim/backend/run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${APP_DIR}/campaignsim/backend</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${APP_DIR}/campaignsim/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/campaignsim-flask.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/campaignsim-flask.err</string>
</dict>
</plist>
PLIST

launchctl unload "${PLIST_PATH}" 2>/dev/null || true
launchctl load "${PLIST_PATH}"

sleep 4
if launchctl list | grep -q "co.campaignsim.flask"; then
  log "Flask backend loaded via launchd"
else
  warn "launchd load may be delayed. Check: tail -f ~/Library/Logs/campaignsim-flask.log"
fi

# =============================================================================
# PHASE 14 — Cloudflare Tunnel
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
cloudflared tunnel create "${TUNNEL_NAME}" 2>/dev/null || warn "Tunnel already exists"

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
cloudflared tunnel route dns "${TUNNEL_NAME}" "${DOMAIN}"

log "Installing cloudflared as launchd service..."
CLOUDFLARED_PLIST="${HOME}/Library/LaunchAgents/com.cloudflare.cloudflared.plist"

cat > "${CLOUDFLARED_PLIST}" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cloudflare.cloudflared</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(command -v cloudflared)</string>
        <string>tunnel</string>
        <string>--config</string>
        <string>${HOME}/.cloudflared/config.yml</string>
        <string>run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/cloudflared.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/cloudflared.err</string>
</dict>
</plist>
PLIST

launchctl unload "${CLOUDFLARED_PLIST}" 2>/dev/null || true
launchctl load "${CLOUDFLARED_PLIST}"

sleep 3
if launchctl list | grep -q "com.cloudflare.cloudflared"; then
  log "Cloudflare Tunnel running via launchd"
else
  warn "Tunnel may still be starting. Check: tail -f ~/Library/Logs/cloudflared.log"
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
echo -e "  App dir:    ${APP_DIR}"
echo ""
echo -e "${YELLOW}Service management (macOS launchd):${NC}"
echo "  Flask logs:     tail -f ~/Library/Logs/campaignsim-flask.log"
echo "  Tunnel logs:    tail -f ~/Library/Logs/cloudflared.log"
echo "  Restart Flask:  launchctl kickstart -k gui/\$(id -u)/co.campaignsim.flask"
echo "  Restart tunnel: launchctl kickstart -k gui/\$(id -u)/com.cloudflare.cloudflared"
echo ""
echo -e "${YELLOW}Update to latest:${NC}"
echo "  cd ${APP_DIR} && git pull origin ${BRANCH}"
echo "  launchctl kickstart -k gui/\$(id -u)/co.campaignsim.flask"
echo ""
