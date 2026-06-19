FROM python:3.11

# Install Node.js (>=18) and build tools
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first to leverage layer caching
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml ./backend/

# Install Node and Python dependencies
# torch is sourced from PyTorch CPU index (see pyproject.toml [tool.uv.sources])
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync

# Copy project source
COPY . .

EXPOSE 3002 5001

# Start frontend and backend concurrently
CMD ["npm", "run", "dev"]
