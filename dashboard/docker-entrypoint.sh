#!/bin/sh
set -eu

exec python -m dashboard.server.main \
  --project "${DASHBOARD_PROJECT}" \
  --host "${DASHBOARD_HOST}" \
  --port "${DASHBOARD_PORT}" \
  "$@"
