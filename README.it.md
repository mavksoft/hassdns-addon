# HassDNS DNS — Add-on per Home Assistant

[![Añadir repositorio a Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmavksoft%2Fhassdns-addon)

Servizio DNS dinamico proprio su **hassdns.com**: mantiene il tuo IP pubblico sempre aggiornato e rinnova il **certificato Let's Encrypt via DNS-01** (TXT tramite API — senza aprire porte) per avere Home Assistant accessibile in HTTPS senza interruzioni.

Un'alternativa indipendente ai DDNS gratuiti: la zona vive sulla nostra infrastruttura DNS (PowerDNS anycast) con API aperta per TXT e IPv4+IPv6.

## Installazione

**Opzione 1 — un click**: usa il pulsante in alto e conferma in Home Assistant.

**Opzione 2 — manuale**: Impostazioni → Componenti aggiuntivi → Store → ⋮ → Repository → aggiungi `https://github.com/mavksoft/hassdns-addon` → installa **HassDNS DNS**.

Poi: crea il tuo sottodominio su [hassdns.com](https://hassdns.com) e copia il **token dell'account**.

## Configurazione

```yaml
domains:
  - mi-casa.hassdns.com
token: "<api_token — 64 hex>"
seconds: 300
lets_encrypt:
  accept_terms: true
  certfile: fullchain.pem
  keyfile: privkey.pem
```

L'add-on:

- pubblica il tuo IP ogni `seconds` secondi (`hassdns.com/update`),
- emette e rinnova il certificato LE con `certbot --manual --preferred-challenges dns` — gli hook pubblicano il TXT `_acme-challenge` via API e lo puliscono dopo,
- copia il certificato in `/ssl/` — compatibile con la config HTTPS di HA e l'add-on NGINX SSL proxy.

## API di aggiornamento

L'endpoint segue il formato standard di update via URL — qualsiasi client dyndns con dominio+token funziona:

```
GET https://hassdns.com/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

- `token`: api_token dell'account (64 hex, tutti i domini) o del record (40 hex).
- `ip` vuoto = IP del chiamante.
- `txt`/`clear` gestiscono il TXT `_acme-challenge.<dom>` (DNS-01).
