#!/usr/bin/env bash
set -Eeuo pipefail
SERVICE=${SERVICE:-lms}
PORT=${PORT:-8000}

# Check TCP port
if ! (echo > "/dev/tcp/127.0.0.1/${PORT}" >/dev/null 2>&1); then
  exit 1
fi

# Verify WSGI imports
python - <<'PY'
import os, sys
svc = os.environ.get('SERVICE','lms')
if svc not in ('lms','cms'):
    sys.exit(1)
mod = f"{svc}.wsgi"
__import__(mod)
PY