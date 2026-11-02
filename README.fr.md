# HassDNS DNS — Add-on pour Home Assistant

[![Añadir repositorio a Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmavksoft%2Fha-cloud-addon)

Service DNS dynamique propre sur **hassdns.com** : maintient votre IP publique à jour et renouvelle le **certificat Let's Encrypt via DNS-01** (TXT par API — sans ouvrir de ports) pour garder votre Home Assistant accessible en HTTPS sans coupures.

Une alternative indépendante aux DDNS gratuits : la zone vit sur notre propre infrastructure DNS (PowerDNS anycast) avec API ouverte pour TXT et IPv4+IPv6.

## Installation

**Option 1 — un clic** : utilisez le bouton ci-dessus et validez dans Home Assistant.

**Option 2 — manuel** : Paramètres → Modules complémentaires → Boutique → ⋮ → Dépôts → ajoutez `https://github.com/mavksoft/ha-cloud-addon` → installez **HassDNS DNS**.

Ensuite : créez votre sous-domaine sur [hassdns.com](https://hassdns.com) et copiez votre **token de compte**.

## Configuration

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

Le module :

- publie votre IP actuelle toutes les `seconds` secondes (`hassdns.com/update`),
- émet et renouvelle le certificat LE via `certbot --manual --preferred-challenges dns` — les hooks publient le TXT `_acme-challenge` par l'API puis le nettoient,
- copie le certificat dans `/ssl/` — compatible avec la config HTTPS de HA et le module NGINX SSL proxy.

## API de mise à jour

L'endpoint suit le format standard d'update par URL — tout client dyndns avec domaine+token fonctionne :

```
GET https://hassdns.com/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

- `token` : api_token du compte (64 hex, tous vos domaines) ou de l'enregistrement (40 hex).
- `ip` vide = IP de l'appelant.
- `txt`/`clear` gèrent le TXT `_acme-challenge.<dom>` (DNS-01).
