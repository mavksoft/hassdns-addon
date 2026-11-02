# HassDNS DNS

DNS dinámico en `hassdns.com` con certificado Let's Encrypt automático.

## Uso

1. Regístrate en [hassdns.com](https://hassdns.com) y crea tu subdominio.
2. Copia el **token de cuenta** (ficha del registro → API).
3. Configura `domains` + `token`, activa `lets_encrypt.accept_terms` y arranca.

El add-on actualiza tu IP cada `seconds` y renueva el cert LE por DNS-01 —
sin abrir puertos. El certificado queda en `/ssl/` listo para HA.

## Opciones

- `domains`: lista de FQDN `*.hassdns.com` tuyos.
- `token`: api_token de tu cuenta (64 hex) o del registro (40 hex).
- `seconds`: intervalo de actualización de IP (mínimo 60).
- `lets_encrypt.accept_terms`: aceptar el ToS de Let's Encrypt.
- `lets_encrypt.certfile` / `keyfile`: nombres en `/ssl/`.
- `lets_encrypt.algo`: `secp384r1` (defecto), `secp256r1` o `rsa`.
