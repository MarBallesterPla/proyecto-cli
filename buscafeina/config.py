"""Configuració d'usuari/ària.

Dos fitxers, tots dos fora del repositori:

- `~/.buscafeina/config.json`: preferències (noconté mai claus secretes).
  Es valida abans d'usar-lo: un JSON roto o un camp equivocat dona un
  missatge humà (ConfigError) en lloc de silencis o tracebacks.
- `.env` (carpeta actual): **claus**. Està en .gitignore des del primer
  commit; `.env.example` documenta quines variables es reconeixen.
  Variables llegides: INFOJOBS_CLIENT_ID, INFOJOBS_CLIENT_SECRET,
  OPENAI_API_KEY.

Els secrets només es lliguen del entorn; mai s'escriuen al config.json ni
s'imprimeixen.
"""

import json
import os
from pathlib import Path

from .errors import ConfigError

CONFIG_DIR = Path.home() / ".buscafeina"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    # URL de la borsa d'ocupació del teu Pacte Comarcal.
    # Hi ha un pacte per comarca; posa ací la URL de la teua.
    "pacte_comarcal_url": "https://avalemterritori.es/acords-territorials/pactes-per-locupacio/",
    "resultats_per_cercador": 10,
    # On busca els fitxers de sortida (relatiu a la carpeta actual)
    "directori_resultats": "resultats",
    # Proveïdor d'IA: "ollama" (local, per defecte) o "openai" (API compatible)
    "proveidor_ia": "ollama",
    # Model per a les accions amb IA
    "model_ia": "qwen3",
    # URL d'Ollama si no és la per defecte
    "ollama_url": "http://localhost:11434",
    # Només si proveidor_ia == "openai"
    "openai_base_url": "https://api.openai.com/v1",
    "openai_api_key_env": "OPENAI_API_KEY",
    # Perfil del candidat/a per a l'avaluació IA (experiència, preferències…)
    "perfil": "",
}

#: camp -> tipus esperat (per a donar missatges útils quan no quadrar)
TYPES = {
    "pacte_comarcal_url": str,
    "resultats_per_cercador": int,
    "directori_resultats": str,
    "proveidor_ia": str,
    "model_ia": str,
    "ollama_url": str,
    "openai_base_url": str,
    "openai_api_key_env": str,
    "perfil": str,
}


def load_dotenv(path: Path | str = ".env") -> None:
    """Carrega claus des d'un fitxer .env senzill (CLAU=valor per línia).

    Les variables que ja existixen al entorn tenen prioritat. No falla si el
    fitxer no existix: s'usen les variables d'entorn del sistema.
    """
    path = Path(path)
    if not path.is_file():
        return
    try:
        for linia in path.read_text(encoding="utf-8").splitlines():
            linia = linia.strip()
            if not linia or linia.startswith("#") or "=" not in linia:
                continue
            clau, _, valor = linia.partition("=")
            clau = clau.strip()
            valor = valor.strip().strip('"').strip("'")
            if clau and clau not in os.environ:
                os.environ[clau] = valor
    except OSError:
        return  # sense .env llegible, seguixim amb l'entorn del sistema


def load_config(path: Path | None = None) -> dict:
    """Config per defecte + config.json, validat. Llança ConfigError si està roto."""
    config = dict(DEFAULTS)
    path = path or CONFIG_PATH
    if not path.exists():
        return config
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise ConfigError(f"No puc llegir {path}: {error.strerror or error}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"El fitxer {path} no és JSON vàlid (línia {error.lineno}): {error.msg}. "
            "Arregla'l o esborra'l per a tornar als valors per defecte."
        )
    if not isinstance(data, dict):
        raise ConfigError(f"El fitxer {path} ha de contindre un objecte JSON ({{…}}).")
    for camp, valor in data.items():
        esperat = TYPES.get(camp)
        if esperat is None:
            continue  # clau desconneguda: l'ignorem, no trenca res
        if camp == "resultats_per_cercador" and isinstance(valor, bool):
            raise ConfigError(f"{path} · «{camp}» ha de ser un nombre, no {valor}.")
        if esperat is int and not isinstance(valor, int):
            raise ConfigError(f"{path} · «{camp}» ha de ser un nombre enter.")
        if esperat is str and not isinstance(valor, str):
            raise ConfigError(f"{path} · «{camp}» ha de ser text.")
        config[camp] = valor
    if config.get("proveidor_ia") not in ("ollama", "openai", "local"):
        raise ConfigError(
            f"{path} · «proveidor_ia» ha de ser «ollama» o «openai», "
            f"no {config['proveidor_ia']!r}."
        )
    assert isinstance(config["resultats_per_cercador"], int)
    return config


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
