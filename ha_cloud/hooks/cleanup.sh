#!/usr/bin/with-contenv bashio
# certbot manual-cleanup-hook: limpia el TXT tras la validación.
set -e
FQDN="${CERTBOT_DOMAIN}"
TOKEN="$(bashio::config 'token')"
SHORT="${FQDN%.ha-cloud.es}"
curl -fsS --max-time 30 \
  "https://api.ha-cloud.es/update?domains=${SHORT}&token=${TOKEN}&clear=true" || true
echo "[ha-cloud] cleanup ${FQDN}"
