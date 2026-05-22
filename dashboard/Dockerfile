# Autoresearch dashboard — multi-stage image for local Docker and cloud deployment.
# Build from repo root:
#   docker build -f dashboard/Dockerfile -t autoresearch-dashboard .
# Run:
#   docker run --rm -p 3847:3847 -v "$(pwd):/workspace:ro" autoresearch-dashboard

FROM node:20-alpine AS web
WORKDIR /build
COPY dashboard/web/package.json dashboard/web/package-lock.json ./
RUN npm ci
COPY dashboard/web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard/requirements.txt ./dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt

COPY dashboard/server ./dashboard/server
COPY dashboard/__init__.py ./dashboard/__init__.py
COPY --from=web /build/dist ./dashboard/web/dist

COPY dashboard/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=3847 \
    DASHBOARD_PROJECT=/workspace

EXPOSE 3847

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3847/api/health', timeout=3)"

ENTRYPOINT ["/entrypoint.sh"]
