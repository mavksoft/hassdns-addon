# HassDNS DNS

DNS dinámico propio (hassdns.com · ha-cloud.es) + certificado Let's Encrypt
automático por **DNS-01** — sin abrir puertos, sin depender de terceros.

## Qué hace

- Actualiza tu IP pública cada `seconds` segundos en uno o varios subdominios.
- Emite y renueva un certificado Let's Encrypt por reto DNS (TXT
  `_acme-challenge` publicado vía API) — vale incluso con CG-NAT.
- Copia el cert a `/ssl/` para que Home Assistant sirva HTTPS válido.
- **Multi-proveedor**: los dominios de zonas externas (`*.duckdns.org` u
  otros proveedores con el formato estándar de update por URL) publican su
  reto por la API de ese proveedor — un solo certificado puede cubrir varios
  hostnames distintos (SANs) aunque vivan en servicios diferentes.

## Instalación

1. Regístrate en [hassdns.com](https://hassdns.com) y crea tu subdominio.
2. Copia el **token** (ficha del registro → API, 40 hex — o el api_token de
   tu cuenta, 64 hex).
3. Configura `domains` + `token`, acepta `lets_encrypt.accept_terms` y arranca.

## Opciones

| Opción | Descripción |
|---|---|
| `domains` | Lista de FQDN tuyos (`*.hassdns.com`, `*.ha-cloud.es`, `*.duckdns.org`). |
| `token` | api_token de cuenta (64 hex) o token del registro (40 hex). |
| `duckdns_token` | Token del proveedor externo — solo si incluyes dominios de esa zona (p. ej. `*.duckdns.org`). |
| `seconds` | Intervalo de actualización de IP (mínimo 60). |
| `lets_encrypt.accept_terms` | Aceptar el ToS de Let's Encrypt (obligatorio para el cert). |
| `lets_encrypt.certfile` / `keyfile` | Nombre destino en `/ssl/` (por defecto `hassdns_fullchain.pem` / `hassdns_privkey.pem`). |
| `lets_encrypt.algo` | `secp384r1` (defecto), `secp256r1` o `rsa`. |

## El certificado — importante

Los nombres por defecto son **propios** (`hassdns_*.pem`): no pisan el
`fullchain.pem`/`privkey.pem` de otros add-ons (DuckDNS oficial, NGINX…).
Apunta tu `http:` de HA a esos ficheros:

```yaml
http:
  ssl_certificate: /ssl/hassdns_fullchain.pem
  ssl_key: /ssl/hassdns_privkey.pem
```

**Un solo cert, varias URLs**: incluye en `domains` todos los hostnames que
quieras — de nuestras zonas o de un proveedor externo compatible (con su
`duckdns_token`) — y certbot emite UN certificado con todos los SANs: todas
las URLs responden con candado.

Si otro add-on ya gestiona `/ssl/fullchain.pem`, o desinstálalo o mantén los
nombres propios y apunta cada servicio a su fichero.

## Migración desde otro add-on DDNS

Si vienes de otro add-on que ya emite a `/ssl/fullchain.pem`:

1. Mantén nuestros nombres propios (`hassdns_fullchain.pem` /
   `hassdns_privkey.pem`) — no hace falta pisar nada.
2. Cambia `http:` para apuntar a los ficheros nuevos y reinicia HA.
3. Si la URL anterior debe seguir funcionando, añade su dominio a `domains`
   con el token del proveedor (`duckdns_token`) — un solo cert cubre ambas.
4. Cuando todo funcione, desinstala el add-on anterior.

## Solución de problemas

| Síntoma | Causa | Arreglo |
|---|---|---|
| `CERTBOT_DOMAIN: unbound` | Versión < 1.1.1 | Actualiza el add-on |
| `NXDOMAIN _acme-challenge` | TXT no publicado | El record debe existir en el panel y la zona `public+verified` |
| `Read-only file system` en `/ssl/` | Versión < 1.1.3 | Actualiza (map `ssl:rw`) |
| `too many failed authorizations` | Rate-limit LE | Espera 1h desde el último intento |
| Solo una URL con candado | Cert sin ese SAN | Añade el dominio a `domains` (+`duckdns_token`) y re-emite |

## Renovación

El add-on renueva el cert automáticamente cuando quedan <30 días (loop diario).
La IP se mantiene aunque el cert falle — son procesos independientes.
