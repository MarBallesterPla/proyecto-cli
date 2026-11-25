"""Motor d'execució: connecta els portals amb l'ordenador sense saber de CLI.

Ací no es printa ni es llig res: només es consulta els portals i es lligan
o escriuen fitxers. La interfaz (cli.py) i les accions (acciones.py)
cruen esta capa.
"""

import csv
import json
from pathlib import Path

from .errors import BuscafeinaError
from .export import FIELDS, _rows, default_stem
from .options import PORTALS
from .portals import get_portal


def consultar_portals(ctx: dict, portals: list[str] | None = None, limit: int = 10) -> list:
    """Torna una llista de tuples (portal, ofertes).

    `portals=None vol dir «fes-ho servir el que hi haja al context» (que al
    seu torn ve dels `--portals` de la línia d'ordes o de tots). Les
    excepcions d'un portal no tomben la sessió: es guarden a `ctx['avisos']`
    i eixe portal queda sense ofertes (fallback al navegador).
    """
    criteria = ctx["criteris"]
    config = ctx["config"]
    noms = portals if portals is not None else ctx.get("portals", list(PORTALS))
    parells = []
    for nom in noms:
        portal = get_portal(nom, criteria, config)
        ofertes = []
        if not portal.browser_only:
            try:
                ofertes = portal.fetch_offers(limit=limit)
            except Exception as error:  # un portal caigut no pot tombar la cerca
                ctx.setdefault("avisos", []).append(f"{portal.label}: {error}")
        parells.append((portal, ofertes))
    return parells


def executar_cerca(ctx: dict, portals: list[str] | None = None, limit: int = 10):
    """Executa la cerca i torna (files_planes, parells)."""
    parells = consultar_portals(ctx, portals=portals, limit=limit)
    return ofertes_plans(parells), parells


def ofertes_plans(parells: list) -> list[dict]:
    """Converteix (portal, ofertes) en files planes amb el camp `portal`."""
    return _rows(parells)


def guardar_export(parells: list, ctx: dict, formats: list[str], directori: str) -> list[Path]:
    """Escriu CSV/JSON i torna els camins creats."""
    from .export import save_results

    return save_results(parells, ctx["criteris"], formats, directory=directori)


def llegir_ofertes(path: Path) -> list[dict]:
    """Llig un fitxer de resultats (CSV o JSON) i torna les files amb ofetes reals.

    Llança BuscafeinaError amb missatge humà si el fitxer no es pot llegir o
    no té la forma esperada.
    """
    path = Path(path)
    if not path.is_file():
        raise BuscafeinaError(f"No trobe el fitxer {path}.")
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise BuscafeinaError(f"No puc llegir {path}: {error.strerror or error}")
    if path.suffix == ".json":
        try:
            rows = json.loads(raw)
        except json.JSONDecodeError as error:
            raise BuscafeinaError(f"JSON invàlid a {path} (línia {error.lineno}): {error.msg}")
        if not isinstance(rows, list):
            raise BuscafeinaError(f"{path} no conté una llista d'ofertes.")
    else:
        rows = list(csv.DictReader(raw.splitlines(), delimiter=";"))
    return [
        row for row in rows
        if isinstance(row, dict) and row.get("titol")
        and "(cerca al navegador)" not in row["titol"]
    ]
