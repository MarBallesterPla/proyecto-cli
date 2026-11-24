"""Configuració d'usuari/ària (a ~/.buscafeina/config.json)."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".buscafeina"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    # URL de la borsa d'ocupació del teu Pacte Comarcal.
    # Hi ha un pacte per comarca; posa ací la URL de la teua.
    "pacte_comarcal_url": "https://avalemterritori.es/acords-territorials/pactes-per-locupacio/",
    "resultats_per_cercador": 10,
    # Model d'Ollama per a "buscafeina avalua"
    "model_ollama": "qwen3",
    # Perfil del candidat/a per a l'avaluació IA (experiència, preferències…)
    "perfil": "",
}


def load_config() -> dict:
    config = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass  # config corrupta: s'utilitzen els valors per defecte
    return config


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
