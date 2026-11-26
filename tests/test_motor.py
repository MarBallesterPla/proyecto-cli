"""Proves del motor: cerca simulada, exportació, neteja destructiva i proves d'IA."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from buscafeina.acciones import Accio
from buscafeina.errors import AccioNoValida, IAError


def _accio(**extra):
    entry = {"nom": "prova", "describe": "acció de prova", "comandos": ["cerca"]}
    entry.update(extra)
    return Accio.from_config(entry)


@pytest.fixture
def ctx(tmp_path):
    from buscafeina.models import Criteria

    return {
        "config": {"proveidor_ia": "ollama", "model_ia": "qwen3", "perfil": ""},
        "criteris": Criteria(keyword="fuster", locality="Xàtiva"),
        "portals": ["InfoJobs"],
        "limit": 5,
        "model": None,
        "perfil": "fuster a Xàtiva",
        "directori": str(tmp_path),
        "formats": ["csv"],
        "fitxers": [],
        "avisos": [],
    }


# ------------------------------------------------------------------ cerca

def test_cerca_en_simulacio_no_toca_res(monkeypatch, ctx):
    """Camí feliç + porta de simulació: `--simulacio` no ha d'anar a la xarxa."""
    def trampa(*a, **k):
        raise AssertionError("en simulació no es pot xafar la xarxa")

    monkeypatch.setattr("buscafeina.motor.consultar_portals", trampa)
    missatge = _accio(efecte="cerca").executar(ctx, simulacio=True)
    assert "simulació" in missatge
    assert "no guardaria res" in missatge


def test_exportar_escriu_i_informa(tmp_path, ctx, ofertes_planes, monkeypatch):
    """Camí feliç: exportar escriu CSV/JSON i el missatge diu el camí."""
    ctx["ofertes"] = ofertes_planes
    ctx["parells"] = []
    ctx["formats"] = ["csv", "json"]
    accio = _accio(efecte="exportar",
                   params={"formats": {"per_defecte": ["csv", "json"]}})
    missatge = accio.executar(ctx)
    assert "Guardades 3 ofertes" in missatge
    escrits = list(Path(tmp_path).glob("*.csv")) + list(Path(tmp_path).glob("*.json"))
    assert len(escrits) == 2
    assert str(escrits[0]) in missatge  # el missatge diu SOBRE QUÈ


def test_exportar_simulacio_no_escriu(tmp_path, ctx, ofertes_planes):
    """Cas felly no tan felly: en simulació no pot apareixer cap fitxer nou."""
    ctx["ofertes"] = ofertes_planes
    ctx["formats"] = ["csv"]
    _accio(efecte="exportar").executar(ctx, simulacio=True)
    assert list(Path(tmp_path).iterdir()) == []


# ------------------------------------------------------------------- IA

def test_accio_ia_se_saltara_avisant(tmp_path, ctx):
    """Sense IA (config apuntant a un port mort) l'acció SE SALTA, no trunca."""
    ctx["config"]["ollama_url"] = "http://127.0.0.1:1"  # port on no hi ha servidor
    ctx["ofertes"] = [{"titol": "x"}]
    missatge = _accio(efecte="avaluar", requereix_ia=True).executar(ctx)
    assert "saltada" in missatge
    assert "IA" in missatge.upper()


def test_parseig_resposta_model_bruta():
    """Camí feliç: la IA embolica el JSON amb text omarkdown → el parseig el treu."""
    from buscafeina.ia import extract_json

    brut = 'Ara mateix ho faig!\n```json\n{"descartats": [2]}\n```\nEspero que ajude.'
    assert extract_json(brut) == {"descartats": [2]}
    think = '<|im_start|>ratiocination</think>{"descartats": []}'
    assert extract_json(think) == {"descartats": []}


def test_extract_json_sense_json_llanca_iaerror():
    """Cas felly: el model no torna JSON → IAError amb els primers 200 caràcters."""
    from buscafeina.ia import extract_json

    with pytest.raises(IAError):
        extract_json("ho sento, no puc ajudar amb això")


# ----------------------------------------------------------------- neteja

def test_neteja_simulada_anuncia_i_no_esborra(tmp_path):
    """Camí feliç + porta destructiva: --simulacio diu què esborraria."""
    vell = tmp_path / "feina-vella.csv"
    vell.write_text("portal;titol\n", encoding="utf-8")
    old = (datetime.now() - timedelta(days=40)).timestamp()
    import os

    os.utime(vell, (old, old))
    ctx = {"config": {}, "directori": str(tmp_path), "fitxers": [], "avisos": []}
    missatge = _accio(efecte="neteja", destructiva=True).executar(ctx, simulacio=True)
    assert "simulació" in missatge and "feina-vella.csv" in missatge
    assert vell.exists()


def test_neteja_destructiva_cal_confirmar(tmp_path, monkeypatch):
    """Cas felly: destructiva sense --si ni confirmació → cancel·lat, intacte."""
    vell = tmp_path / "feina-vella.csv"
    vell.write_text("portal;titol\n", encoding="utf-8")
    import os

    old = (datetime.now() - timedelta(days=40)).timestamp()
    os.utime(vell, (old, old))
    monkeypatch.setattr("buscafeina.acciones._confirmar", lambda accio, consola: False)
    ctx = {"config": {}, "directori": str(tmp_path), "fitxers": [], "avisos": []}
    missatge = _accio(efecte="neteja", destructiva=True).executar(ctx)
    assert "cancel·lat" in missatge
    assert vell.exists()
    # i amb --si, sí que esborra
    missatge = _accio(efecte="neteja", destructiva=True).executar(ctx, confirmat=True)
    assert "Esborrats 1 fitxers" in missatge
    assert not vell.exists()


def test_efecte_desconegut_no_passa():
    """Cas felly: un efecte inventat a l'JSON → AccioNoValida amb la llista permesa."""
    with pytest.raises(AccioNoValida) as exc_info:
        _accio(efecte="telepatia")
    assert "telepatia" in str(exc_info.value)


def test_moure_no_sobreescriu(tmp_path):
    """Cas felly: fitxer que ja existix a la destinació → sufix horari, no pèrdua."""
    from buscafeina.acciones import _sense_colisio

    dest = tmp_path / "arxiu"
    dest.mkdir()
    (dest / "feina.csv").write_text("vell", encoding="utf-8")
    nou = _sense_colisio(dest, Path("feina.csv"))
    assert nou != dest / "feina.csv"
    assert nou.name.startswith("feina-")


# --------------------------------------------------- IA amb proveïdor simulat

def test_accio_avaluar_amb_proveidor_simulat(tmp_path, ctx, ofertes_planes, proveidor_fals):
    """Camí feliç d'IA: el proveïdor simulat puntua, ordena i l'acció escriu el rànquing."""
    proveidor_fals["proveidor"].resposta = json.dumps({
        "avaluacions": [
            {"id": 1, "puntuacio": 9, "motiu": "encaixa amb el perfil"},
            {"id": 2, "puntuacio": 4, "motiu": "lluny del perfil"},
            {"id": 3, "puntuacio": 7, "motiu": "acceptable"},
        ]
    })
    ctx["ofertes"] = ofertes_planes
    missatge = _accio(efecte="avaluar", requereix_ia=True).executar(ctx)
    assert proveidor_fals["proveidor"].crides  # el proveïdor s'ha cridat de veritat
    assert "Avaluades 3 ofertes" in missatge
    assert "9/10" in missatge  # el resum comença per la millor (ordenació descendent)
    fitxers = list(Path(tmp_path).glob("avaluades-*.csv"))
    assert len(fitxers) == 1
    contingut = fitxers[0].read_text(encoding="utf-8-sig")
    assert "encaixa amb el perfil" in contingut  # el motiu arriba al CSV


def test_accio_filtrar_amb_proveidor_simulat(ctx, ofertes_planes, proveidor_fals):
    """Camí feliç d'IA: la IA descarta l'oferta 2 i l'acció en deixa 2 de 3."""
    proveidor_fals["proveidor"].resposta = json.dumps({"descartats": [2]})
    ctx["ofertes"] = ofertes_planes
    missatge = _accio(efecte="filtrar", requereix_ia=True).executar(ctx)
    assert "Filtrades 3 ofertes" in missatge
    assert "en queden 2" in missatge
    assert len(ctx["ofertes"]) == 2  # la descartada és l'índex 1 (id 2)
