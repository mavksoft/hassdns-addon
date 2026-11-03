#!/usr/bin/env bash
# certbot manual-cleanup-hook: limpia el TXT tras la validación.
# TOKEN/API exportados por run.sh; CERTBOT_DOMAIN lo pone certbot.
set -e
curl -fsS --max-time 30 \
  "${API:-https://hassdns.com}/update?domains=${CERTBOT_DOMAIN}&token=${TOKEN}&clear=true" || true
echo "[hassdns] cleanup ${CERTBOT_DOMAIN}"
