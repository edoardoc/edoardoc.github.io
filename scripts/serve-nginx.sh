#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
WORKDIR="${TMPDIR:-/tmp}/500nits-nginx-${PORT}"

if ! command -v nginx >/dev/null 2>&1; then
  echo "nginx is not installed or is not on PATH."
  echo "Install nginx, then run: bash scripts/serve-nginx.sh"
  exit 1
fi

mkdir -p \
  "${WORKDIR}/logs" \
  "${WORKDIR}/client_body_temp" \
  "${WORKDIR}/proxy_temp" \
  "${WORKDIR}/fastcgi_temp" \
  "${WORKDIR}/uwsgi_temp" \
  "${WORKDIR}/scgi_temp"

cat > "${WORKDIR}/nginx.conf" <<EOF
pid "${WORKDIR}/nginx.pid";
error_log "${WORKDIR}/logs/error.log" warn;

events {
  worker_connections 1024;
}

http {
  default_type application/octet-stream;
  access_log "${WORKDIR}/logs/access.log";
  sendfile on;

  types {
    text/html html htm;
    text/css css;
    application/javascript js mjs;
    application/json json;
    application/pdf pdf;
    image/svg+xml svg;
    image/jpeg jpg jpeg;
    image/png png;
    image/gif gif;
    image/x-icon ico;
    text/plain txt;
  }

  server {
    listen ${HOST}:${PORT};
    server_name localhost 500nits.com www.500nits.com;
    root "${ROOT}";
    index index.html;

    add_header Cache-Control "no-store";

    location / {
      try_files \$uri \$uri/ =404;
    }
  }
}
EOF

echo "Serving ${ROOT}"
echo "Open http://${HOST}:${PORT}/"
exec nginx -p "${WORKDIR}" -c "${WORKDIR}/nginx.conf" -g "daemon off;"
