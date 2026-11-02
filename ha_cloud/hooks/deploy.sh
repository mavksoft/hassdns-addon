#!/usr/bin/with-contenv bashio
# certbot manual-auth-hook: publica el TXT _acme-challenge.<fqdn> vía API.
# CERTBOT_DOMAIN (ej. mi-casa.hassdns.com) — el endpoint reconoce el FQDN de
# cualquiera de nuestras zonas, así que se envía completo (zona-agnóstico).
set -e
FQDN="${CERTBOT_DOMAIN}"
TOKEN="$(bashio::config 'token')"
RESP=$(curl -fsS --max-time 30 \
  "https://api.hassdns.com/update?domains=${FQDN}&token=${TOKEN}&txt=${CERTBOT_TOKEN}" || true)
echo "[hassdns] deploy ${FQDN} → ${RESP}"
# TTL 60s — espera a que el TXT propague antes de que LE lo compruebe.
sleep 65
