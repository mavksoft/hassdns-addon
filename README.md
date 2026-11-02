# HA Cloud DNS — Add-on para Home Assistant

Réplica del add-on oficial **DuckDNS** sobre `ha-cloud.es`: mantiene tu IP
actualizada y renueva el certificado **Let's Encrypt por DNS-01** (TXT vía API,
sin abrir puertos) — acceso remoto HTTPS siempre válido, sin depender de terceros.

## Instalación

1. Home Assistant → **Ajustes → Add-ons → Tienda de add-ons** → menú ⋮ →
   **Repositorios** → añade:
   ```
   https://github.com/mavksoft/ha-cloud-addon
   ```
2. Busca **HA Cloud DNS** → Instalar.
3. Crea tu subdominio en [ha-cloud.es](https://ha-cloud.es) (portal DNS) y
   copia tu **token de cuenta** (rec_api.php → `?a=token`).

## Configuración

```yaml
domains:
  - mi-casa.ha-cloud.es
token: "<tu api_token de 64 hex>"
seconds: 300
lets_encrypt:
  accept_terms: true
  certfile: fullchain.pem
  keyfile: privkey.pem
```

El add-on:
- cada `seconds` llama `api.ha-cloud.es/update?domains=…&token=…&ip=` (IP auto),
- emite/renueva el cert LE con `certbot --manual --preferred-challenges dns`
  (hooks que publican `_acme-challenge.<dom>` TXT vía `&txt=`/`&clear=true`),
- copia el cert a `/ssl/` — compatible con la config HTTPS de HA y el
  add-on NGINX Home Assistant SSL proxy.

## Endpoint compatible DuckDNS

Cualquier cliente que soporte DuckDNS funciona cambiando dominio+token:

```
GET https://api.ha-cloud.es/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

`token` = api_token de la cuenta (64 hex, sirve para todos tus dominios) o
token del registro (40 hex).
