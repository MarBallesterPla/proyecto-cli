# Changelog

Totes les notes importants d'este projecte.
Format [Keep a Changelog](https://keepachangelog.com/ca/1.1.0/),
adherit a [Versionat Semàntic](https://semver.org/lang/ca/).

## [1.1.0] - 2026-11-25

### Afegit

- **Dos portals nous amb lectura automàtica**: `SEPE` (Sistema Nacional
  d'Empleu, agregat públic de tots els serveis autonòmics, inclòs Labora) i
  `Turijobs` (turisme i hostaleria, amb forta presència a la Comunitat
  Valenciana). La CLI ara llegeix ofertes de 4 portals i manté el recorregut
  alternatiu al navegador en els altres 2 (Labora amb sessió DNI/PIN i Pacte
  Comarcal).
- L'acció `cerca-portals` admet una funció de cerca injectable
  (`ctx["cercar"]`) per a provar el pipeline sense xarxa ni portals reals.
- Noves proves unitàries dels analitzadors SEPE/Turijobs amb HTML fixture
  (sense xarxa): taules del SNE, empresa/ciutat de Turijobs i filtre de
  localitat.

### Corregit

- `--portals` de la línia d'ordes guanyava ara als portals per defecte
  declarats en `accions.json` (abans se consultaven els 6 sempre).
- `--guardar csv` produïx només CSV (abans exportava també JSON per respectar
  el `per_defecte` del JSON extern).
- `motor.exportar` escrivia amb el `formats` del context en lloc del de
  l'acció.

## [1.0.0] - 2026-11-24

### Afegit

- **Accions predefinides en JSON extern** (`accions.json`) amb esquema propi
  (`buscafeina/data/esquema-accions.json`) validat abans d'executar. ADR-001
  justifica la decisió.
- Noves accions de fàbrica: `cerca-portals`, `exportar-fitxers`,
  `avaluar-perfil`, `filtrar-descart`, `neteja-vells`, `arxivar-sessio`,
  `tot-el-dia`; encadenables amb `despres` i executables una a una amb
  `--exec`.
- **Mode simulació** (`--simulacio`) en totes les accions; les destructives
  (`neteja`, `moure`) demanen `--si` o confirmació interactiva.
- **Capa d'IA desacoplada** (`buscafeina/ia.py`): Ollama local per defecte o
  API compatible amb OpenAI; claus només per `.env`/variables d'entorn, amb
  `.env.example`. ADR-002.
- Sense IA o sense xarxa: les accions amb IA se salten amb avís llegible i la
  CLI continua amb la resta.
- Excepcions pròpies (`BuscafeinaError`, `ConfigError`, `AccioNoValida`,
  `IAError`) amb missatges humans i codis de sortida; cap traceback davant
  errors previsibles.
- Subcomandos `cerca`, `tot`, `neteja`, `accions` a més de `avalua`.
- 33 proves amb pytest en carpetes temporals i CI en GitHub Actions (Python
  3.10 i 3.12).
- Instal·lació com a comanda amb `uv tool install` / `pipx install` des de
  GitHub.

### Canviat

- `avalua` fa servir ara la capa d'IA comuna i admet `--simulacio`,
  `--filtrar` i `--llistar-accions`.
- Els noms dels fitxers de resultats porten segons per a no sobreescriure mai
  una exportació prèvia.

## [0.1.0]

- Versió inicial: cerca en Labora, InfoJobs, Pacte Comarcal i LinkedIn,
  exportació CSV/JSON i avaluació amb Ollama.
