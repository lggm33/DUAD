#!/usr/bin/env sh
set -eu

if [ -z "${PORT:-}" ]; then
  echo "Missing required env var: PORT" >&2
  exit 1
fi

envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'


