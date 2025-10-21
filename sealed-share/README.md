# Sealed Share

Turvallinen tiedoston- ja viestinjaon palvelu, jossa:

- Vain varmistettu vastaanottaja (sähköposti/OIDC) voi avata ja ladata sisällön
- Aikarajat ja kertakäyttöisyys tuettu
- Vesileimaus (watermark) tiedostoihin
- Linkkijaon esto (vain suora vastaanottaja pääsee)

## Toimitukset

- Web-palvelu (FastAPI, Python) ja/tai CLI
- Vastaanottajan varmistus: sähköposti (magic link, toteutettu) tai OIDC (esim. Google, tulossa)

## Sähköpostin asetukset

Palvelu tarvitsee SMTP-tiedot ympäristömuuttujina:

- `SEALED_SHARE_SMTP_HOST` – SMTP-palvelimen osoite
- `SEALED_SHARE_SMTP_PORT` – SMTP-portti (oletus 587)
- `SEALED_SHARE_SMTP_USER` – SMTP-käyttäjätunnus
- `SEALED_SHARE_SMTP_PASS` – SMTP-salasana
- `SEALED_SHARE_FROM` – Lähettäjän sähköposti (oletus: käyttäjätunnus)
- `SEALED_SHARE_MAGIC_LINK_BASE` – Linkin perus-URL (oletus: http://localhost:8080)
- Vesileimaus: PDF/kuvaan dynaamisesti
- Infra: Docker Compose, ohjeet

## Hakemistorakenne

- `web/` – Web-palvelun koodi (FastAPI)
- `cli/` – CLI-työkalu (Python)
- `infra/` – Docker Compose, konfiguraatio
- `README.md` – tämä tiedosto
- `docs/` – käyttöohjeet ja arkkitehtuuri
