# REFERÈNCIA DEL PROJECTE — buscafeina

> Document generat a partir de la sessió de treball de novembre de 2026.
> Resum de tot el que s'ha fet, per què, i com continuar-ho.

## 1. Què és buscafeina

CLI en Python per a buscar feina en valencià, amb quatre cercadors:
**Labora** (Punt Labora, GVA), **InfoJobs**, **Pacte Comarcal** i **LinkedIn**.

Estratègia triada («ambdós, amb fallback»):
1. Mostrar resultats **al terminal** quan el portal ho permet.
2. Si no és possible (bloqueig, sessió pròpia…), **obrir el navegador**
   amb la cerca filtrada.

## 2. Estructura del codi

```
proyecto-cli/
├── buscafeina.cmd            # llançador per a Windows (python -m buscafeina %*)
├── pyproject.toml            # paquet instal·lable; comanda: buscafeina
├── README.md                 # documentació d'ús
└── buscafeina/
    ├── cli.py                # flux: prompts → cerca → taules → navegador → guardar
    ├── models.py             # Criteria (criteris) i Offer (oferta)
    ├── options.py            # opcions dels menús + traducció de filtres per portal
    ├── config.py             # ~/.buscafeina/config.json
    ├── export.py             # exportació a CSV i JSON (carpeta resultats/)
    └── portals/
        ├── base.py           # Portal (ABC), slugify, http_get, PortalError
        ├── infojobs.py       # API oficial o rascat SSR + filtre local de localitat
        ├── linkedin.py       # endpoint públic "jobs-guest"
        ├── labora.py         # només navegador (formulari amb sessió)
        └── pacte.py          # només navegador (URL configurable)
```

Dependències: `requests`, `questionary`, `rich`, `beautifulsoup4`.
Python 3.15 instal·lat a la màquina.

## 3. Descobriments tècnics (important per a mantindre-ho)

### LinkedIn
- Endpoint públic sense sessió:
  `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&location=...&start=0`
- Retorna HTML amb targetes: `.base-search-card__title`,
  `.base-search-card__subtitle`, `.job-search-card__location`,
  `a.base-card__full-link`, `time[datetime]`.
- Sí que respecta `location`. Filtre `f_JT`:
  F=complet, P=parcial, C=contracte, I=pràctiques, T=temporal, O=altres.
- URL de navegador: `https://www.linkedin.com/jobs/search/?keywords=...&location=...&f_JT=...`

### InfoJobs
- **La URL amb path combinat** (`/ofertas-trabajo/panadero/en-valencia`)
  dispara el captxà anti-bot (Distil). **No usar-la.**
- La URL amb query string sí funciona (200 amb contingut SSR):
  `https://www.infojobs.net/ofertas-trabajo?keyword=...&where=...`
- Però el filtre `where` **no** s'aplica al servidor: el fa el seu
  JavaScript al navegador. Per això el rascat trau diverses pàgines
  (fins a 3) i filtra per localitat en local; si cap coincidix, mostra
  totes amb un avís.
- Classes del HTML SSR: `li.ij-OfferList-offerCardItem`,
  enllaços amb `/of-i`, detalls a `li[class*='description-list-item']`.
- **API oficial (opcional, el millor)**: `https://api.infojobs.net/api/9/offer`
  amb Basic Auth `INFOJOBS_CLIENT_ID` / `INFOJOBS_CLIENT_SECRET`
  (clau gratuïta a developer.infojobs.net). Paràmetres usats:
  `q`, `city`, `contractType`, `workday`, `maxResults`, `order`.
  Slugs: indefinido, temporal, practicas, autonomo, otros-contratos /
  completa, parcial, por-horas.
- Fa limitació de peticions: després de varies peticions ràpides servix
  la pàgina de «No podemos identificar tu navegador» (el fallback ho
  gestiona).

### Labora (Punt Labora)
- El cercador és un formulari en passos amb sessió pròpia
  (`puntlabora.gva.es/consoferta/consulta`, POST a `/consoferta/consulta/comarca`).
  Necessita DNI+PIN per a postular-se → **només navegador**.
- El formulari té camps: `puesto`, `provincia`, `localidad`, `tipoJornada`,
  `idiomas`, `carnetConducir`, `discapacidad`, `mostrarEuropa`.

### Pacte Comarcal
- No existix un cercador unificat: cada comarca té el seu pacte i la seua
  borsa. El portal aggregator és avalemterritori.es (WordPress informatiu).
- Es configura la URL pròpia a `~/.buscafeina/config.json`
  → clau `"pacte_comarcal_url"`.

## 4. Decisions de disseny

- **Torn i horari**: cap portal gran té filtre natiu → s'afeixen al text
  de la cerca (p. ex. «panadero torn de nit»). `Criteria.keyword_terms()`.
- **Prompts resistents**: `questionary` falla en terminals no interactius
  (l'error salta en *construir* el prompt, no només en `.ask()`).
  `_ask(lambda: questionary.select(...), default=...)` ho embolica tot i
  usa valors per defecte si no hi ha terminal interactiu.
- **CSV pensat per a Excel**: codificació `utf-8-sig` i separador `;`.
- **JSON**: llista d'ofertes, `ensure_ascii=False`, indent 2.
- Els portals sense lectura automàtica es guarden igualment als fitxers
  amb la seua URL de cerca (titol «(cerca al navegador)»).

## 5. Comandes

```powershell
buscafeina                     # cerca interactiva (menús en valencià)
buscafeina -k "cambrer/a" -l "València" --guardar
buscafeina --guardar csv       # csv | json | ambdos (defecte: ambdos)
buscafeina --portals "LinkedIn,InfoJobs" --limit 5 --no-browser
buscafeina --help
```

Opcions: `-k` paraula clau, `-l` localitat, `--contracte`, `--jornada`,
`--torn`, `--horari`, `--portals`, `--limit`, `--guardar`, `--no-browser`.

Els resultats ixen a `resultats/` amb nom i data
(p. ex. `feina-panadero-valencia-20261110-1403.csv`).

## 6. Problemes resolts durant la sessió

| Problema | Solució |
| --- | --- |
| pip exigia README.md per a instal·lar | es va crear README.md |
| `buscafeina` no estava al PATH | s'ha afegit `C:\Users\mar_b\AppData\Roaming\Python\Python315\Scripts` al PATH d'usuari + llançador `buscafeina.cmd` al projecte |
| `questionary` petava sense terminal interactiu | `_ask()` embolica construcció + `.ask()` amb valor per defecte |
| InfoJobs ignorava `where` en el rascat | rascat de fins a 3 pàgines + filtre de localitat en local + avís a l'usuari |
| walrus confús a infojobs.py | refet amb `has_api_credentials()` |

## 7. Idees per a continuar

- [x] **Avaluador IA amb Ollama** — implementat: `buscafeina avalua`
      (mòdul `buscafeina/avalua.py`; envia totes les ofertes en una sola
      petició a `/api/chat` amb `format: json` i `think: false`; guarda
      `resultats/avaluades-<data>.csv`).
- [ ] Configurar la URL real del Pacte Comarcal de la teua comarca.
- [ ] Registrar-se a developer.infojobs.net i usar l'API (INFOJOBS_CLIENT_ID/SECRET).
- [ ] Guardar les preferències de cerca (recordar l'última cerca).
- [ ] Deduplicar ofertes repetides entre cerques successives.
- [ ] Notificacions de noves ofertes: cerca programada + comparació amb
      les anteriors.
- [ ] Afegir més portals (Indeed, Turijobs, Jooble…) creant una nova
      classe a `portals/` i registrant-la a `portals/__init__.py`.
- [ ] La carpeta git arrela a `C:\Users\mar_b` (tot el directori d'usuari):
      considerar `git init` propi dins de `proyecto-cli`.

## 8. Estat actual

- Instal·lat i funcional (provat amb LinkedIn, InfoJobs, Labora i Pacte).
- PATH arreglat (cal obrir finestra nova de PowerShell).
- Cap comissió de git feta (el repo arrela al directori d'usuari).
