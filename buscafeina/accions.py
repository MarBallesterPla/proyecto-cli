"""Accions predefinides de buscafeina, definides en un fitxer JSON extern.

El fitxer d'accions (`accions.json`) es busca en este ordre:

1. La variable d'entorn `BUSCAFEINA_ACCIONS`.
2. `./accions.json` (carpeta actual).
3. `~/.buscafeina/accions.json`.
4. `buscafeina/data/accions.json` (accions d'exemple incloses en el paquet).

Es valida amb `jsonschema` (esquema propi en buscafina/data/esquema-accions.json,
documentat al README) **abans** d'executar res: si l'esquema no passa, els
missatges diuen exactament quin camp falla.

Cada acció declara:

- `comandos`: quins subcomandaments l'executen (`cerca`, `avalua`, `neteja`…)
- `requereix_ia`: si necessita el proveïdor d'IA (si no hi ha IA, es salta amb
  un avís, mai trenca la seqüència)
- `simulable`: si accepta `--simulacio` (mostra què faria sense tocar res)
- `destructiva`: si esborra o sobreescriu (cal `--simulacio`, `--si` o
  confirmació interactiva abans d'actuar)
- `despres`: accions que s'encadenen automàticament després d'esta (combinables)
- `params`: valor per defecte i permesos de cada paràmetre

Afegir una acció nova **no exigeix tocar el codi**: només cal afegir una
entrada al JSON que declare quins paràmetres rep, quins comandaments
l'executen i quines accions s'encadenen després.
"""

import json
import os
from pathlib import Path

from .errors import AccioNoValida, ConfigError

try:  # jsonschema és obligatori; l'avís només cobreix entorns molt minimalistes
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

PARAM_KEYS = {
    "directori", "formats", "perfil", "model", "limit",
    "dies", "portals", "keyword", "localitat",
}

#: fitxer d'esquema i accions d'exemple del paquet
DATA_DIR = Path(__file__).parent / "data"
ESQUEMA_PATH = DATA_DIR / "esquema-accions.json"
ACCIONS_EXEMPLE_PATH = DATA_DIR / "accions.json"

ENV_VAR = "BUSCAFEINA_ACCIONS"
PROJECT_FILE = Path("accions.json")
USER_FILE = Path.home() / ".buscafeina" / "accions.json"


def ruta_accions() -> Path:
    """On és el fitxer d'accions que es carregarà (primer trobat)."""
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env)
    if PROJECT_FILE.is_file():
        return PROJECT_FILE
    if USER_FILE.is_file():
        return USER_FILE
    return ACCIONS_EXEMPLE_PATH


def cargar_accions(path: Path | None = None) -> dict:
    """Llig i valida el fitxer d'accions. Llança ConfigError amb camp i motiu."""
    path = Path(path) if path else ruta_accions()
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise ConfigError(f"No puc llegir {path}: {error.strerror or error}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ConfigError(f"JSON invàlid a {path} (línia {error.lineno}): {error.msg}")
    if jsonschema is not None:
        try:
            esquema = json.loads(ESQUEMA_PATH.read_text(encoding="utf-8"))
        except OSError as error:
            raise ConfigError(f"Falta l'esquema {ESQUEMA_PATH}: {error}")
        except json.JSONDecodeError as error:
            raise ConfigError(f"Esquema invàlid a {ESQUEMA_PATH} (línia {error.lineno}): {error.msg}")
        try:
            jsonschema.validate(data, esquema)
        except jsonschema.ValidationError as error:
            camp = "/".join(str(p) for p in error.absolute_path) or "<arrel>"
            raise ConfigError(f"{path} · camp «{camp}»: {error.message}")
    else:  # sense jsonschema: validació mínima de totes maneres
        _validacio_base(data, path)
    return data


def _validacio_base(data, path: Path) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("accions"), list) or not data["accions"]:
        raise ConfigError(f"{path}: falta la llista «accions»")
    for index, action in enumerate(data["accions"]):
        for camp in ("nom", "comandos", "describe"):
            if camp not in action:
                raise ConfigError(f"{path} · accions[{index}]: falta el camp «{camp}»")


def accions_per_comando(data: dict, comando: str) -> list:
    """Llista d'Accio permeses per al comando indicat, ordenades per «ordre»."""
    from .acciones import Accio

    result = []
    for entry in data["accions"]:
        if comando not in entry.get("comandos", []):
            continue
        result.append(Accio.from_config(entry))
    result.sort(key=lambda a: a.ordre)
    return result


def accio_anomenada(data: dict, comando: str, nom: str):
    """Busca una acció pel seu nom (per a `buscafeina cerca -x nom` / `--exec`)."""
    for entry in data["accions"]:
        if entry.get("nom") == nom:
            if comando not in entry.get("comandos", []):
                raise AccioNoValida(
                    f"L'acció «{nom}» no es pot executar amb «{comando}» "
                    f"(permesa per a: {', '.join(entry.get('comandos', []))})."
                )
            from .acciones import Accio

            return Accio.from_config(entry)
    disponibles = [e["nom"] for e in data["accions"] if comando in e.get("comandos", [])]
    raise AccioNoValida(
        f"No hi ha cap acció anomenada «{nom}» per a «{comando}». "
        f"Disponibles: {', '.join(disponibles) or 'cap'}."
    )


def listar(data: dict) -> list:
    return [entry["nom"] for entry in data["accions"]]
