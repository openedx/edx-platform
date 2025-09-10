#!/usr/bin/env bash
set -Eeuo pipefail

log() { echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

SERVICE=${SERVICE:-lms}
PORT=${PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-info}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-2}
RUN_MIGRATIONS=${RUN_MIGRATIONS:-false}
SKIP_ASSETS=${SKIP_ASSETS:-true}

if [[ "$SERVICE" != "lms" && "$SERVICE" != "cms" ]]; then
  fail "SERVICE must be 'lms' or 'cms' (got '$SERVICE')"
fi

# Choose WSGI module and gunicorn config
if [[ "$SERVICE" == "lms" ]]; then
  export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-lms.envs.postgres}
  WSGI_MODULE="lms.wsgi:application"
  GUNICORN_CONF="conf/gunicorn_lms.conf.py"
else
  export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-cms.envs.postgres}
  WSGI_MODULE="cms.wsgi:application"
  GUNICORN_CONF="conf/gunicorn_cms.conf.py"
fi

# Optionally build frontend assets
if [[ "$SKIP_ASSETS" != "true" ]]; then
  log "Installing Node dependencies and building assets (NODE_ENV=${NODE_ENV:-production})"
  if command -v npm >/dev/null 2>&1; then
    # Prefer clean installs but fallback to install for legacy trees
    (npm ci || npm install) && npm run build || log "Asset build failed; continuing"
  else
    log "npm not found; skipping asset build"
  fi
else
  log "Skipping asset build per SKIP_ASSETS=${SKIP_ASSETS}"
fi

# Optionally run migrations
if [[ "$RUN_MIGRATIONS" == "true" ]]; then
  log "Applying Django migrations for $SERVICE"
  python manage.py "$SERVICE" migrate --noinput || log "Migrations failed; continuing"
fi

# Print Django checks (non-fatal) to surface config issues early
python manage.py "$SERVICE" check || log "Django system checks reported issues"

# Start gunicorn
log "Starting Gunicorn for $SERVICE on 0.0.0.0:${PORT} (workers=${WEB_CONCURRENCY}, loglevel=${LOG_LEVEL})"
exec gunicorn \
  --config "${GUNICORN_CONF}" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --log-level "${LOG_LEVEL}" \
  "${WSGI_MODULE}"