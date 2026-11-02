# HA Cloud DNS — Add-on für Home Assistant

[![Añadir repositorio a Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmavksoft%2Fha-cloud-addon)

Eigener dynamischer DNS-Dienst auf **ha-cloud.es**: hält deine öffentliche IP immer aktuell und erneuert das **Let's-Encrypt-Zertifikat über DNS-01** (TXT per API — ohne offene Ports), damit dein Home Assistant unterbrechungsfrei per HTTPS erreichbar bleibt.

Eine unabhängige Alternative zu kostenlosen DDNS-Diensten: die Zone läuft auf unserer eigenen DNS-Infrastruktur (PowerDNS Anycast) mit offener API für TXT sowie IPv4+IPv6.

## Installation

**Option 1 — ein Klick**: Button oben nutzen und in Home Assistant bestätigen.

**Option 2 — manuell**: Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories → `https://github.com/mavksoft/ha-cloud-addon` hinzufügen → **HA Cloud DNS** installieren.

Danach: Subdomain auf [ha-cloud.es](https://ha-cloud.es) anlegen und dein **Konto-Token** kopieren.

## Konfiguration

```yaml
domains:
  - mi-casa.ha-cloud.es
token: "<api_token — 64 hex>"
seconds: 300
lets_encrypt:
  accept_terms: true
  certfile: fullchain.pem
  keyfile: privkey.pem
```

Das Add-on:

- veröffentlicht alle `seconds` Sekunden deine aktuelle IP (`api.ha-cloud.es/update`),
- stellt das LE-Zertifikat aus und erneuert es per `certbot --manual --preferred-challenges dns` — die Hooks setzen das `_acme-challenge`-TXT über die API und räumen es danach auf,
- kopiert das Zertifikat nach `/ssl/` — kompatibel mit der HTTPS-Konfig von HA und dem NGINX-SSL-Proxy-Add-on.

## Update-API

Der Endpoint folgt dem Standard-Update-URL-Format — jeder dyndns-Client mit Domain+Token funktioniert:

```
GET https://api.ha-cloud.es/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

- `token`: Konto-api_token (64 hex, alle Domains) oder Record-Token (40 hex).
- `ip` leer = IP des Aufrufers.
- `txt`/`clear` verwalten das TXT `_acme-challenge.<dom>` (DNS-01).
