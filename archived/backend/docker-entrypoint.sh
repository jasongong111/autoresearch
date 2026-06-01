#!/bin/sh
set -eu

ARGS=""
if [ -n "${DASHBOARD_TRANSCRIPTS_DIR:-}" ] && [ -d "${DASHBOARD_TRANSCRIPTS_DIR}" ]; then
  ARGS="$ARGS --transcripts-dir ${DASHBOARD_TRANSCRIPTS_DIR}"
fi

exec python -m backend.app.main \
  --project "${DASHBOARD_PROJECT}" \
  --host "${DASHBOARD_HOST}" \
  --port "${DASHBOARD_PORT}" \
  $ARGS \
  "$@"
