# Sealed Share – Arkkitehtuuri

## Yleiskuvaus

Sealed Share on turvallinen tiedoston- ja viestinjaon palvelu, jossa:

- Vain varmistettu vastaanottaja voi avata sisällön
- Aikarajat ja kertakäyttöisyys tuettu
- Vesileimaus tiedostoihin
- Linkkijaon esto

## Komponentit

- **Web-palvelu (FastAPI)**: Tarjoaa REST-rajapinnan jakamiseen ja vastaanottamiseen
- **CLI-työkalu**: Mahdollistaa jakamisen komentoriviltä
- **Infra**: Docker Compose, mahdollinen pilvitallennus

## Tietoturvaominaisuudet

- Sähköpostivarmistus (magic link) – vastaanottajalle lähetetään kertakäyttöinen linkki sähköpostilla (SMTP)
- OIDC (tulossa)
- Vesileimaus PDF/kuvaan (tulossa)
- Kertakäyttöisyys ja aikarajat
- Linkkijaon esto: vastaanottajan sähköpostin/OIDC:n tarkistus

## Laajennettavuus

- Pilvitallennus (esim. S3) voidaan lisätä myöhemmin
- OIDC-integraatio mahdollista
- Sähköpostin lähetys SMTP:llä, asetukset ympäristömuuttujina

## Tiedostorakenne

- `web/` – Web-palvelu
- `cli/` – CLI-työkalu
- `infra/` – Docker Compose
- `docs/` – Dokumentaatio
