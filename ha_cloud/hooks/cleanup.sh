#!/usr/bin/with-contenv bashio
# certbot manual-cleanup-hook: limpia el TXT tras la validación.
set -e
FQDN="${CERTBOT_DOMAIN}"
TOKEN="$(bashio::config 'token')"
curl -fsS --max-time 30 \
  "https://api.hassdns.com/update?domains=${FQDN}&token=${TOKEN}&clear=true" || true
echo "[hassdns] cleanup ${FQDN}"
