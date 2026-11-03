# Changelog

## 1.1.0
- Rebranding a HassDNS (hassdns.com como marca principal).
- Multi-zona: acepta dominios hassdns.com y ha-cloud.es; endpoint canónico hassdns.com (zona-agnóstico, envía el FQDN completo).

## 1.0.0
- Primera versión: update de IP + certificado Let's Encrypt por DNS-01.

## 1.2.0
- Nombres de cert únicos por defecto (`hassdns_fullchain.pem`/`hassdns_privkey.pem`) — sin colisión con otros add-ons.
- Multi-proveedor DNS-01: dominios `*.duckdns.org` enrutan a la API de DuckDNS (`duckdns_token`) — un cert con SANs cruzados.
- `map: ssl:rw` — /ssl escribible.
