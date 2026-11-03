# Changelog

## 1.3.7
- Logo: nuevo banner con contenedor cápsula oscuro y borde cian, con texto «HassDNS» completo y legible tanto en modo claro como oscuro de Home Assistant.
- Navegación: el botón «Volver a la ficha del add-on» redirige directamente a la vista de información y controles del complemento (`/hassio/addon/ha_cloud/info`).

## 1.3.6
- Fix CSS: estilo global para inputs (sin depender de type=text explícito), altura uniforme de 44px y control de autofill de llaveros/navegadores para mantener el tema oscuro.

## 1.3.5
- Rediseño completo de la interfaz ingress: paridad visual con hassdns.com (fondo sutil de red y domótica, tarjeta centrada en ambos ejes con glassmorphism, tipografía General Sans).
- Botón «Volver a Home Assistant» en la cabecera y tarjeta para retroceder y salir del panel sin quedar atrapado en la vista Ingress.

## 1.3.4
- Dockerfile: copia /panel + apk python3 (la UI daba 502 Bad Gateway — app.py no existia en la imagen).

## 1.3.3
- duckdns_token traducido en los 6 idiomas (aparecía crudo sin traducción).

## 1.3.2
- DOCS/README actualizados al flujo login/register del panel.

## 1.3.1
- Registro de cuenta embebido en el panel (api_register.php + auto-login).

## 1.3.0
- Panel propio por ingress (login usuario+pass → api_token+dominios a /data, password nunca persiste, config 600) + run.sh usa la config del panel como override.

## 1.2.0
- Nombres de cert únicos por defecto (`hassdns_fullchain.pem`/`hassdns_privkey.pem`) — sin colisión con otros add-ons.
- Multi-proveedor DNS-01: dominios `*.duckdns.org` enrutan a la API de DuckDNS (`duckdns_token`) — un cert con SANs cruzados.
- `map: ssl:rw` — /ssl escribible.

## 1.1.0
- Rebranding a HassDNS (hassdns.com como marca principal).
- Multi-zona: acepta dominios hassdns.com y ha-cloud.es; endpoint canónico hassdns.com (zona-agnóstico, envía el FQDN completo).

## 1.0.0
- Primera versión: update de IP + certificado Let's Encrypt por DNS-01.
