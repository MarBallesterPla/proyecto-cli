"""Proves de la configuració: per defecte, valors validats i secrets fora del codi."""

import json

import pytest

from buscafeina.config import DEFAULTS, load_config
from buscafeina.errors import ConfigError


def test_config_inexistent_dona_per_defecte(tmp_path):
    """Camí feliç: sense config.json, els valors per defecte."""
    config = load_config(tmp_path / "no-hi-ha.json")
    assert config["model_ia"] == DEFAULTS["model_ia"]
    assert config["proveidor_ia"] == "ollama"


def test_config_valid_sobreix_per_defecte(tmp_path):
    """Camí feliç: un config vàlid sobreescriu només el que diu."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"perfil": "fuster", "resultats_per_cercador": 5}),
                    encoding="utf-8")
    config = load_config(path)
    assert config["perfil"] == "fuster"
    assert config["resultats_per_cercador"] == 5
    assert config["model_ia"] == DEFAULTS["model_ia"]  # la resta, intacta


def test_cas_felly_config_rota(tmp_path):
    """Cas felly: JSON roto → ConfigError llegible que diu línia i fitxer."""
    path = tmp_path / "config.json"
    path.write_text("{perfil: fuster}", encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_config(path)
    assert "línia" in str(exc_info.value)
    assert str(path) in str(exc_info.value)


def test_cas_felly_camp_de_tipus_equivocat(tmp_path):
    """Cas felly: «resultats_per_cercador» amb text → ConfigError que anomena el camp."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"resultats_per_cercador": "molts"}), encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_config(path)
    assert "resultats_per_cercador" in str(exc_info.value)


def test_cas_felly_proveidor_ia_desconegut(tmp_path):
    """Cas felly: «proveidor_ia» inventat → ConfigError amb els valors permesos."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"proveidor_ia": "chatgpt"}), encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_config(path)
    assert "ollama" in str(exc_info.value) and "openai" in str(exc_info.value)


def test_cap_claus_a_DEFAULTS():
    """Els secrets no moren al codi: ni DEFAULTS ni la clau de config «api_key»."""
    assert not any("api_key" in k or "secret" in k for k in DEFAULTS)
    assert not any("secret" in str(v).lower() for v in DEFAULTS.values())
