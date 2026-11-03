#!/usr/bin/env bash
# certbot manual-auth-hook (DNS-01): publica el TXT _acme-challenge.<fqdn> vía API.
# TOKEN y API los exporta run.sh; CERTBOT_DOMAIN y CERTBOT_VALIDATION los pone
# certbot. NO usar with-contenv aquí: resetea el entorno y pierde las CERTBOT_*.
set -e
RESP=$(curl -fsS --max-time 30 \
  "${API:-https://hassdns.com}/update?domains=${CERTBOT_DOMAIN}&token=${TOKEN}&txt=${CERTBOT_VALIDATION}" || true)
echo "[hassdns] deploy ${CERTBOT_DOMAIN} → ${RESP}"
# TTL 60s — espera a que el TXT propague antes de que LE lo compruebe.
sleep 65
