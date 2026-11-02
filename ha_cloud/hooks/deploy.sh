#!/usr/bin/with-contenv bashio
# certbot manual-auth-hook: publica el TXT _acme-challenge.<fqdn> vía API.
# CERTBOT_DOMAIN (ej. mi-casa.ha-cloud.es) → nombre corto dentro de la zona.
set -e
FQDN="${CERTBOT_DOMAIN}"
TOKEN="$(bashio::config 'token')"
SHORT="${FQDN%.ha-cloud.es}"
RESP=$(curl -fsS --max-time 30 \
  "https://api.ha-cloud.es/update?domains=${SHORT}&token=${TOKEN}&txt=${CERTBOT_TOKEN}" || true)
echo "[ha-cloud] deploy ${FQDN} → ${RESP}"
# TTL 60s — espera a que el TXT propague antes de que LE lo compruebe.
sleep 65
