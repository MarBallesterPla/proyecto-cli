# Changelog

Totes les notes importants d'este projecte.
Format [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
adherido a [Versionado Semántico](https://semver.org/lang/es/).

## [1.1.0] - 2026-11-25

### Añadido

- **Dos portales nuevos con lectura automática**: `SEPE` (Sistema Nacional de
  Empleo, agregado público de todos los servicios autonómicos, incluido
  Labora) y `Turijobs` (turismo y hostelería, con fuerte presencia en la
  Comunitat Valenciana). La CLI ahora lee ofertas de 4 portales y mantiene
  el fallback a navegador en los otros 2 (Labora con sesión DNI/PIN y Pacte
  Comarcal).
- La acción `cerca-portals` acepta una función de búsqueda inyectable
  (`ctx["cercar"]`) para probar el pipeline sin red ni portales reales.
- Nuevas pruebas unitarias de los parsers SEPE/Turijobs con HTML fixture
  (sin red): tablas del SNE, empresa/ciudad de Turijobs y filtro de
  localidad.

### Corregido

- `--portals` de la línea de órdenes ganaba ahora a los portales por defecto
  declarados en `accions.json` (antes se consultaban los 6 siempre).
- `--guardar csv` produce solo CSV (antes exportaba también JSON por
  respetar el `per_defecte` del JSON externo).
- `motor.exportar` escribía con el `formats` del contexto en lugar del de la
  acción.

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
