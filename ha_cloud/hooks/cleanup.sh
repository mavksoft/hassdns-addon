#!/usr/bin/env bash
# certbot manual-cleanup-hook: retira el TXT tras validar.
set -e
FQDN="${CERTBOT_DOMAIN}"
case "$FQDN" in
  *.duckdns.org)
    SUB="${FQDN%.duckdns.org}"
    curl -fsS --max-time 30 \
      "https://www.duckdns.org/update?domains=${SUB}&token=${DDNS_TOKEN_DUCK}&txt=&clear=true" || true
    ;;
  *)
    curl -fsS --max-time 30 \
      "${API:-https://hassdns.com}/update?domains=${FQDN}&token=${TOKEN}&clear=true" || true
    ;;
esac
echo "[hassdns] cleanup ${FQDN}"
