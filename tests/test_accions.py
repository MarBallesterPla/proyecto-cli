"""Proves del fitxer d'accions: càrrega, esquema i errors."""

import json

import pytest

from buscafeina.accions import cargar_accions
from buscafeina.errors import ConfigError

ESQUEMA = json.loads(
    (pytest.__path__ and __import__("pathlib").Path(__file__).parent.parent
     / "buscafeina" / "data" / "esquema-accions.json").read_text(encoding="utf-8")
)


def _esescrigui(tmp_path, nom, dades):
    path = tmp_path / nom
    path.write_text(json.dumps(dades, ensure_ascii=False), encoding="utf-8")
    return path


def test_esquema_accepta_el_fitxer_d_exemple():
    """Camí feliç: l'accion.json del paquet valida contra el seu propi esquema."""
    from pathlib import Path

    data = Path(__file__).parent.parent / "buscafeina" / "data" / "accions.json"
    ruta_cargada = cargar_accions(data)
    assert len(ruta_cargada["accions"]) >= 6
    noms = [a["nom"] for a in ruta_cargada["accions"]]
    assert "avaluar-perfil" in noms and "neteja-vells" in noms


def test_cas_fell_json_roto(tmp_path):
    """Cas felly: JSON mal formattat → ConfigError que diu el motiu, no traceback."""
    path = tmp_path / "accions.json"
    path.write_text('{"esquema": 1, "accions": [', encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        cargar_accions(path)
    assert "JSON invàlid" in str(exc_info.value)
    assert str(path) in str(exc_info.value)


def test_cas_felly_falta_camp_obligatori(tmp_path):
    """Cas felly: a una acció li falta «efecte» → l'error assenyala accions/0."""
    path = _esescrigui(tmp_path, "accions.json",
                      {"esquema": 1, "accions": [{"nom": "x", "describe": "quatre"}]})
    with pytest.raises(ConfigError) as exc_info:
        cargar_accions(path)
    assert "accions/0" in str(exc_info.value)
    assert "efecte" in str(exc_info.value)


def test_cas_felly_efecte_desconegut(tmp_path):
    """Cas felly: un efecte que no existix al motor → l'error llista els permesos."""
    path = _esescrigui(tmp_path, "accions.json", {
        "esquema": 1,
        "accions": [{"nom": "x", "describe": "què fa", "efecte": "palla",
                     "comandos": ["cerca"]}],
    })
    with pytest.raises(ConfigError) as exc_info:
        cargar_accions(path)
    assert "palla" in str(exc_info.value)


def test_cas_felly_comando_no_permes(tmp_path):
    """Cas felly: executar una acció des d'un comando on no està → AccioNoValida."""
    from buscafeina.accions import accio_anomenada
    from buscafeina.errors import AccioNoValida

    path = _esescrigui(tmp_path, "accions.json", {
        "esquema": 1,
        "accions": [{"nom": "neteja-vells", "describe": "què fa", "efecte": "neteja",
                     "comandos": ["neteja"]}],
    })
    data = cargar_accions(path)
    with pytest.raises(AccioNoValida) as exc_info:
        accio_anomenada(data, "cerca", "neteja-vells")
    assert "neteja" in str(exc_info.value)
