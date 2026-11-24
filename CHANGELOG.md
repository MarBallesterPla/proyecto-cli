# Changelog

Totes les notes importants d'este projecte.
Format [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
adherido a [Versionado Semántico](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-24

### Añadido

- **Acciones predefinidas en JSON externo** (`accions.json`) con esquema propio
  (`buscafeina/data/esquema-accions.json`) validado antes de ejecutar.
  ADR-001 justifica la decisión.
- Nuevas acciones de fábrica: `cerca-portals`, `exportar-fitxers`,
  `avaluar-perfil`, `filtrar-descart`, `neteja-vells`, `arxivar-sessio`,
  `tot-el-dia`; encadenables con `despres` y ejecutables una a una con `--exec`.
- **Modo simulación** (`--simulacio`) en todas las acciones; las destructivas
  (`neteja`, `moure`) piden `--si` o confirmación interactiva.
- **Capa de IA desacoplada** (`buscafeina/ia.py`): Ollama local por defecto o
  API compatible con OpenAI; claves solo por `.env`/variables de entorno, con
  `.env.example`. ADR-002.
- Sin IA o sin red: las acciones con IA se saltan con aviso legible y la CLI
  sigue con el resto.
- Excepciones propias (`BuscafeinaError`, `ConfigError`, `AccioNoValida`,
  `IAError`) con mensajes humanos y códigos de salida; ningún traceback ante
  errores previsibles.
- Subcomandos `cerca`, `tot`, `neteja`, `accions` además de `avalua`.
- 27 pruebas con pytest en carpetas temporales y CI en GitHub Actions
  (Python 3.10 y 3.12).
- Instalación como comando con `uv tool install` / `pipx install` desde GitHub.

### Cambiado

- `avalua` usa ahora la capa de IA común y admite `--simulacio`, `--filtrar` y
  `--llistar-accions`.
- Los nombres de los ficheros de resultados llevan segundos para no
  sobrescribir nunca un export previo.

## [0.1.0]

- Versión inicial: búsqueda en Labora, InfoJobs, Pacte Comarcal y LinkedIn,
  exportación CSV/JSON y evaluación con Ollama.
