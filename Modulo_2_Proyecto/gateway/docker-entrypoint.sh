#!/usr/bin/env sh
set -eu

if [ -z "${PORT:-}" ]; then
  echo "Missing required env var: PORT" >&2
  exit 1
fi

if [ -z "${FRONTEND_UPSTREAM:-}" ]; then
  echo "Missing required env var: FRONTEND_UPSTREAM" >&2
  exit 1
fi

if [ -z "${BACKEND_UPSTREAM:-}" ]; then
  echo "Missing required env var: BACKEND_UPSTREAM" >&2
  exit 1
fi

envsubst '${PORT} ${FRONTEND_UPSTREAM} ${BACKEND_UPSTREAM}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'


