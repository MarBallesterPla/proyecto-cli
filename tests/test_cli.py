"""Proves del CLI: subcomandaments, errors llegibles i cap traceback."""

import pytest

from buscafeina import cli


def test_sense_args_es_cerca(tmp_path, monkeypatch):
    """Camí feliç: `buscafeina` a seques equival a `buscafeina cerca`."""
    monkeypatch.chdir(tmp_path)
    comando, args = cli.parse_args([])
    assert comando == "cerca"
    assert args.simulacio is False


def test_avalua_rep_els_seus_args():
    """El dispatch de `avalua` no es menja els arguments."""
    comando, args = cli.parse_args(["avalua", "-m", "qwen3:4b", "--simulacio"])
    assert comando == "avalua"
    assert "--simulacio" in args and "qwen3:4b" in args


def test_portals_invalides_sortida_2(capsys):
    """Cas felly: portal inventat → missatge legible, exit code 2, zero traceback."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["cerca", "--portals", "Infojob", "--simulacio"])
    assert exc_info.value.code == 2
    eixida = capsys.readouterr().out
    assert "Portals desconeguts" in eixida
    assert "Traceback" not in eixida


def _cerca_buida(ctx, portals=None, limit=10):
    """Motor fals: (files planes, parells) amb una sola oferta fictícia.

    Les files planes són la llista de dicts que `AccioExportar` espera trobar
    a `ctx['ofertes']` després d'una cerca real.
    """
    from buscafeina.models import Offer
    from buscafeina.portals.base import Portal

    class PortalFictici(Portal):
        label = "Fictici"

        def browser_url(self):
            return "https://e.example"

    portal = PortalFictici(ctx["criteris"], {})
    oferta = Offer(title="Fuster d'arxa", url="https://e.example/o",
                   company="Fustes Sud", location="Xàtiva")
    files = [{"portal": "Fictici", "titol": oferta.title, "empresa": oferta.company,
              "lloc": oferta.location, "data": "", "detalls": "", "url": oferta.url}]
    return files, [(portal, [oferta])]


def test_exportar_formats_del_comando(tmp_path, monkeypatch, capsys):
    """Cas felly: --guardar csv ha de produir només CSV tot i que l'JSON diga csv+json.

    Les opcions de la línia d'ordes guanyen als valors per defecte de la
    configuració externa: si no, la CLI ignoraria l'usuari/ària.
    """
    monkeypatch.chdir(tmp_path)
    # el context admet una funció de cerca injectada (`cercar`): les proves
    # l'usen per a no dependre de la xarxa ni dels portals.
    monkeypatch.setattr(cli, "_ctx_from", lambda args, config: {
        **_ctx_base(tmp_path), "formats": ["csv"], "cercar": _cerca_buida})
    cli.main(["cerca", "-k", "fuster", "--no-browser", "--guardar", "csv"])
    escrits = sorted(f.suffix for f in tmp_path.iterdir())
    assert escrits == [".csv"]


def _ctx_base(tmp_path):
    from buscafeina.models import Criteria

    return {
        "config": {"proveidor_ia": "ollama", "model_ia": "qwen3", "perfil": ""},
        "criteris": Criteria(keyword="fuster"),
        "portals": ["Fictici"],
        "limit": 5,
        "model": None,
        "perfil": "",
        "directori": str(tmp_path),
        "formats": None,
        "fitxers": [],
        "avisos": [],
    }


def test_accions_json_rota_no_rebenta(capsys, tmp_path, monkeypatch):
    """Cas felly: JSON de accions roto → ConfigError llegible, mai traceback."""
    trencat = tmp_path / "accions.json"
    trencat.write_text('{"esquema": 1, "accions": [{"no": "hi ha efecte"}]}',
                       encoding="utf-8")
    monkeypatch.setenv("BUSCAFEINA_ACCIONS", str(trencat))
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["accions"])
    assert exc_info.value.code == 2
    assert "accions/0" in capsys.readouterr().out  # l'error assenyala l'element concret


def test_cerca_simulada_funciona_d_princip_a_fin(tmp_path, monkeypatch, capsys):
    """Camí feliç: `cerca --simulacio` acaba be i no escriu fitxers."""
    monkeypatch.chdir(tmp_path)
    cli.main(["cerca", "--simulacio", "--no-browser", "-k", "fuster", "-l", "Xàtiva"])
    eixida = capsys.readouterr().out
    assert "Consultaria" in eixida
    assert list(tmp_path.iterdir()) == []  # res escrit


def test_neteja_simulada_dirigeix_els_paths(tmp_path, monkeypatch, capsys):
    """`neteja --simulacio` no toca res i informa sobre QUIN directori."""
    monkeypatch.chdir(tmp_path)
    cli.main(["neteja", "--simulacio"])
    eixida = capsys.readouterr().out.lower()
    assert "resultats" in eixida or "no existix" in eixida
