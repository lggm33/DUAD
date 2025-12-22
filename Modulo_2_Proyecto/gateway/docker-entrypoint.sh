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

# Nginx resolves hostnames at startup unless proxy_pass uses a variable + resolver.
# Railway services behind *.railway.internal can change their backing IPs after redeploys.
# We derive DNS resolvers from /etc/resolv.conf so Nginx can re-resolve at runtime.
RESOLVER="$(awk '/^nameserver[[:space:]]+/{print $2}' /etc/resolv.conf | paste -sd' ' -)"
if [ -z "${RESOLVER:-}" ]; then
  echo "Could not determine DNS resolver from /etc/resolv.conf" >&2
  exit 1
fi
export RESOLVER

envsubst '${PORT} ${FRONTEND_UPSTREAM} ${BACKEND_UPSTREAM} ${RESOLVER}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'


