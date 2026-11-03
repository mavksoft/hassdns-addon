#!/usr/bin/with-contenv bashio
set -e

API="https://hassdns.com"
LE_DIR="/data/letsencrypt"
DDNS_TOKEN_DUCK="$(bashio::config 'duckdns_token' 2>/dev/null || echo '')"

# El panel de login (ingress) escribe domains/token en las OPCIONES del add-on
# vía Supervisor API y reinicia; esas opciones son la fuente única de verdad.
# Se arranca siempre —también sin configurar— para poder entrar a hacer login.
python3 /panel/app.py &

TOKEN="$(bashio::config 'token')"
SECONDS_WAIT="$(bashio::config 'seconds')"
CERTFILE="$(bashio::config 'lets_encrypt.certfile')"
KEYFILE="$(bashio::config 'lets_encrypt.keyfile')"
DOMAINS=()
for d in $(bashio::config 'domains'); do DOMAINS+=("$d"); done

# Los hooks de certbot (bash plano) heredan estas variables del entorno.
export TOKEN API DDNS_TOKEN_DUCK

# ── Certificado Let's Encrypt por DNS-01 (TXT vía API, enruta por proveedor) ──
issue_cert() {
    bashio::config 'lets_encrypt.accept_terms' || { bashio::log.info "lets_encrypt.accept_terms=false — sin cert"; return 0; }
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
        -d "$(IFS=,; echo "${DOMAINS[*]}")" --cert-name "${DOMAINS[0]}" \
        && rm -f "/ssl/$CERTFILE" "/ssl/$KEYFILE" \
        && cp -L "$LE_DIR/live/${DOMAINS[0]}/fullchain.pem" "/ssl/$CERTFILE" \
        && cp -L "$LE_DIR/live/${DOMAINS[0]}/privkey.pem"  "/ssl/$KEYFILE" \
        && bashio::log.info "Cert LE → /ssl/$CERTFILE"
}

# Actualiza la IP de un dominio enrutando por proveedor (propio / DuckDNS).
update_one() {
    local d="$1" r
    case "$d" in
        *.duckdns.org)
            r=$(curl -fsS --max-time 30 "https://www.duckdns.org/update?domains=${d%.duckdns.org}&token=${DDNS_TOKEN_DUCK}&ip=" || true) ;;
        *)
            r=$(curl -fsS --max-time 30 "${API}/update?domains=${d}&token=${TOKEN}&ip=" || true) ;;
    esac
    [ "$r" = "OK" ] && bashio::log.info "IP al día ($d)" || bashio::log.warning "Update KO ($d): $r"
}

# ── Sin configurar: mantener vivo el panel para que el usuario haga login ─────
if [ "${#DOMAINS[@]}" -eq 0 ] || [ -z "$TOKEN" ]; then
    bashio::log.info "Sin configurar todavía. Abre el panel «HassDNS» en la barra lateral y haz login para elegir tus subdominios."
    wait
    exit 0
fi

# ── Loop: IP al día + renovación del cert ────────────────────────────────────
DOMAIN_CSV=$(IFS=,; echo "${DOMAINS[*]}")
bashio::log.info "HassDNS DNS iniciado — dominios: ${DOMAIN_CSV} (cada ${SECONDS_WAIT}s)"
issue_cert || true
LAST_CERT=$(date +%s)
while true; do
    for d in "${DOMAINS[@]}"; do update_one "$d"; done
    if [ $(( $(date +%s) - LAST_CERT )) -gt 86400 ]; then
        issue_cert || true
        LAST_CERT=$(date +%s)
    fi
    sleep "$SECONDS_WAIT"
done
