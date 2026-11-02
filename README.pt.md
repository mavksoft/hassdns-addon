# HA Cloud DNS — Add-on para Home Assistant

[![Añadir repositorio a Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmavksoft%2Fha-cloud-addon)

Serviço DNS dinâmico próprio em **ha-cloud.es**: mantém o teu IP público sempre atualizado e renova o **certificado Let's Encrypt por DNS-01** (TXT via API — sem abrir portas) para que o teu Home Assistant fique acessível por HTTPS sem cortes.

Uma alternativa independente aos DDNS gratuitos: a zona vive na nossa infraestrutura DNS própria (PowerDNS anycast) com API aberta para TXT e IPv4+IPv6.

## Instalação

**Opção 1 — um clique**: usa o botão acima e confirma no Home Assistant.

**Opção 2 — manual**: Definições → Add-ons → Loja → ⋮ → Repositórios → adiciona `https://github.com/mavksoft/ha-cloud-addon` → instala **HA Cloud DNS**.

Depois: cria o teu subdomínio em [ha-cloud.es](https://ha-cloud.es) e copia o **token da conta**.

## Configuração

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

O add-on:

- publica o teu IP atual a cada `seconds` segundos (`api.ha-cloud.es/update`),
- emite e renova o certificado LE com `certbot --manual --preferred-challenges dns` — os hooks publicam o TXT `_acme-challenge` pela API e limpam-no depois,
- copia o certificado para `/ssl/` — compatível com a config HTTPS do HA e o add-on NGINX SSL proxy.

## API de atualização

O endpoint segue o formato padrão de update por URL — qualquer cliente dyndns com domínio+token funciona:

```
GET https://api.ha-cloud.es/update?domains=mi-casa&token=<token>&ip=<ip|vacío>
    [&ipv6=<ipv6>][&txt=<texto>][&clear=true]  →  "OK" | "KO"
```

- `token`: api_token da conta (64 hex, todos os domínios) ou do registo (40 hex).
- `ip` vazio = IP do chamador.
- `txt`/`clear` gerem o TXT `_acme-challenge.<dom>` (DNS-01).
