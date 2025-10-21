# Sealed Share – Käyttöohjeet

## Web-palvelu

1. Käynnistä palvelu Dockerilla:
   ```sh
   cd infra
   docker-compose up --build
   ```
2. Luo jako (POST /share):
   - Vastaanottajan sähköposti, aikaraja, vesileima, tiedostonimi, sisältö
3. Vastaanottaja saa sähköpostiinsa magic linkin, jolla avaa jaon:
   - Linkki on kertakäyttöinen ja voimassa vain määräajan
   - Linkin klikkaus vie suoraan jaon avaamiseen (tuleva endpoint: /magic/{token})

## CLI

- Jaa tiedosto/viesti:
  ```sh
  python cli/main.py share --recipient user@example.com --filename test.txt --content "salainen viesti"
  ```
- Avaa jako:
  ```sh
  python cli/main.py access --token <token> --recipient user@example.com
  ```

## Ominaisuudet

- Vain varmistettu vastaanottaja pääsee sisältöön (magic link sähköpostilla)
- Aikarajat ja kertakäyttöisyys
- Vesileimaus (tulossa)
- Linkkijaon esto (tulossa)

## Sähköpostin asetukset

Palvelu tarvitsee SMTP-tiedot ympäristömuuttujina:

- `SEALED_SHARE_SMTP_HOST` – SMTP-palvelimen osoite
- `SEALED_SHARE_SMTP_PORT` – SMTP-portti (oletus 587)
- `SEALED_SHARE_SMTP_USER` – SMTP-käyttäjätunnus
- `SEALED_SHARE_SMTP_PASS` – SMTP-salasana
- `SEALED_SHARE_FROM` – Lähettäjän sähköposti (oletus: käyttäjätunnus)
- `SEALED_SHARE_MAGIC_LINK_BASE` – Linkin perus-URL (oletus: http://localhost:8080)
