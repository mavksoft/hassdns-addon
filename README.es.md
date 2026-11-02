# HA Cloud DNS — Add-on para Home Assistant

[![Añadir repositorio a Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmavksoft%2Fha-cloud-addon)

Servicio DNS dinámico propio sobre **ha-cloud.es**: mantiene tu IP pública siempre actualizada y renueva el certificado **Let's Encrypt por DNS-01** (TXT vía API — sin abrir puertos) para que tu Home Assistant quede accesible por HTTPS sin cortes.

Es una alternativa independiente a los DDNS gratuitos: la zona vive en nuestra propia infraestructura DNS (PowerDNS anycast), con API abierta para TXT e IPv4+IPv6.

## Instalación

**Opción 1 — un click**: usa el botón de arriba y acepta en Home Assistant.

**Opción 2 — manual**: Ajustes → Add-ons → Tienda de add-ons → menú ⋮ → Repositorios → añade `https://github.com/mavksoft/ha-cloud-addon` → instala **HA Cloud DNS**.

Después: crea tu subdominio en [ha-cloud.es](https://ha-cloud.es) y copia tu **token de cuenta**.

## Configuración

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

El add-on:

- cada `seconds` segundos publica tu IP actual (`api.ha-cloud.es/update`),
- emite y renueva el certificado LE con `certbot --manual --preferred-challenges dns` — los hooks publican el `_acme-challenge` TXT por la API y lo limpian tras validar,
- copia el cert a `/ssl/` — compatible con la config HTTPS de HA y el add-on NGINX SSL proxy.

## API de actualización

El endpoint sigue el formato estándar de update por URL — cualquier cliente dyndns con dominio+token funciona:

```
GET https://api.ha-cloud.es/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

- `token`: api_token de la cuenta (64 hex, todos tus dominios) o del registro (40 hex).
- `ip` vacío = la IP de quien llama.
- `txt`/`clear` gestionan el TXT `_acme-challenge.<dom>` (DNS-01).
