#!/usr/bin/env bash
# certbot manual-auth-hook (DNS-01): publica _acme-challenge.<fqdn> TXT.
# Enruta por zona: hassdns.com/ha-cloud.es → API propia; duckdns.org → API de DuckDNS.
set -e
FQDN="${CERTBOT_DOMAIN}"
case "$FQDN" in
  *.duckdns.org)
    SUB="${FQDN%.duckdns.org}"
    RESP=$(curl -fsS --max-time 30 \
      "https://www.duckdns.org/update?domains=${SUB}&token=${DDNS_TOKEN_DUCK}&txt=${CERTBOT_VALIDATION}" || true)
    echo "[hassdns] deploy ${FQDN} → duckdns API → ${RESP}"
    ;;
  *)
    RESP=$(curl -fsS --max-time 30 \
      "${API:-https://hassdns.com}/update?domains=${FQDN}&token=${TOKEN}&txt=${CERTBOT_VALIDATION}" || true)
    echo "[hassdns] deploy ${FQDN} → ${RESP}"
    ;;
esac
sleep 65
