#!/usr/bin/with-contenv bashio
set -e

TOKEN="$(bashio::config 'token')"
SECONDS_WAIT="$(bashio::config 'seconds')"
CERTFILE="$(bashio::config 'lets_encrypt.certfile')"
KEYFILE="$(bashio::config 'lets_encrypt.keyfile')"

DOMAINS=()
for d in $(bashio::config 'domains'); do
    DOMAINS+=("$d")
done
[ "${#DOMAINS[@]}" -gt 0 ] || { bashio::log.fatal "Configura al menos un dominio (hassdns.com o ha-cloud.es)"; exit 1; }
[ -n "$TOKEN" ] || { bashio::log.fatal "Falta el token"; exit 1; }

# El endpoint acepta FQDN de cualquiera de nuestras zonas públicas, así que
# enviamos el dominio completo (zona-agnóstico): mi-casa.hassdns.com, etc.
DOMAIN_CSV=$(IFS=,; echo "${DOMAINS[*]}")
API="https://hassdns.com"
LE_DIR="/data/letsencrypt"

# ── Certificado Let's Encrypt por DNS-01 (TXT vía API HassDNS) ───────────────
issue_cert() {
    bashio::config 'lets_encrypt.accept_terms' || { bashio::log.info "lets_encrypt.accept_terms=false — sin cert"; return 0; }
    local args=(-d)
    args+=("$(IFS=,; echo "${DOMAINS[*]}")")
    mkdir -p "$LE_DIR"
    certbot certonly --non-interactive --agree-tos \
        --register-unsafely-without-email \
        --config-dir "$LE_DIR" --work-dir "$LE_DIR/work" --logs-dir "$LE_DIR/logs" \
        --manual --preferred-challenges dns \
        --manual-auth-hook /hooks/deploy.sh \
        --manual-cleanup-hook /hooks/cleanup.sh \
        --key-type "$( [ "$(bashio::config 'lets_encrypt.algo')" = "rsa" ] && echo rsa || echo ecdsa )" \
        --elliptic-curve "$(bashio::config 'lets_encrypt.algo')" \
        --server "$(bashio::config 'lets_encrypt.server')" \
        "${args[@]}" --cert-name "${DOMAINS[0]}" \
        && rm -f "/ssl/$CERTFILE" "/ssl/$KEYFILE" \
        && cp -L "$LE_DIR/live/${DOMAINS[0]}/fullchain.pem" "/ssl/$CERTFILE" \
        && cp -L "$LE_DIR/live/${DOMAINS[0]}/privkey.pem"  "/ssl/$KEYFILE" \
        && bashio::log.info "Cert LE → /ssl/$CERTFILE"
}

# ── Loop: IP al día + renovación del cert ────────────────────────────────────
# Config guardada por el panel (login con usuario+password → api_token+dominios)
if [ -f /data/panel_config.json ]; then
  PC=$(python3 -c "import json,sys;c=json.load(open('/data/panel_config.json'));print(c.get('api_token','')+'|'+','.join(d['name'] for d in c.get('domains',[]) if 'selected' not in c or d['name'] in c['selected']))" 2>/dev/null || true)
  PTOK="${PC%%|*}"; PDOMS="${PC#*|}"
  if [ -n "$PTOK" ] && [ "$PTOK" != "$PC" ]; then TOKEN="$PTOK"; export TOKEN; fi
  if [ -n "$PDOMS" ] && [ "$PDOMS" != "$PC" ]; then IFS=',' read -ra DOMAINS <<< "$PDOMS"; fi
fi
export TOKEN API DDNS_TOKEN_DUCK
bashio::log.info "HassDNS DNS iniciado — dominios: ${DOMAINS[*]} (cada ${SECONDS_WAIT}s)"
DDNS_TOKEN_DUCK=$(bashio::config 'duckdns_token' 2>/dev/null || echo '')
python3 /panel/app.py &
export TOKEN API DDNS_TOKEN_DUCK   # los hooks de certbot (bash plano) los heredan del entorno
issue_cert || true
LAST_CERT=$(date +%s)
while true; do
    RESP=$(curl -fsS --max-time 30 \
        "${API}/update?domains=${DOMAIN_CSV}&token=${TOKEN}&ip=" || true)
    [ "$RESP" = "OK" ] && bashio::log.info "IP actualizada (${DOMAIN_CSV})" \
                      || bashio::log.warning "Update KO: ${RESP}"
    # renovación de cert: reintento diario (LE gestiona la ventana de 60 días)
    if [ $(( $(date +%s) - LAST_CERT )) -gt 86400 ]; then
        issue_cert || true
        LAST_CERT=$(date +%s)
    fi
    sleep "$SECONDS_WAIT"
done
