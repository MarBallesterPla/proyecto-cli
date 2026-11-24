"""Avaluació d'ofertes amb IA (subcomandament `buscafeina avalua`).

Ús:
    buscafeina avalua                          # el fitxer més recent
    buscafeina avalua resultats/fitxer.csv     # un fitxer concret
    buscafeina avalua -p "2 anys en forneria" --model qwen3 --simulacio
    buscafeina avalua --llistar-accions

La mecànica de l'IA viu a buscafeina/ia.py (proveïdor Ollama local o API
compatible amb OpenAI, clau només per entorn); este mòdul conté la lògica de
negoci — puntuar, filtrar i guardar — que també reutilitza el motor d'accions.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .config import load_config
from .errors import BuscafeinaError, IAError
from .ia import ProveidorIA, extract_json

console = Console()

SYSTEM_PROMPT_AVALUAR = """Ets un conseller d'ocupació. Rebràs una llista d'ofertes \
de treball numerades i el perfil d'una persona candidata.
Per a cada oferta has de:
1. Puntuar de 0 a 10 l'adequació per a la persona candidata (10 = encaixa perfecta).
2. Donar un motiu breu en valencià (màxim 15 paraules).
Respon SEMPRE només amb JSON vàlid, sense markdown ni text extra, amb esta \
forma exacta:
{"avaluacions": [{"id": 1, "puntuacio": 7, "motiu": "exemple de motiu"}, \
{"id": 2, "puntuacio": 3, "motiu": "exemple de motiu"}]}
L'"id" ha de coincidir amb l'id de cada oferta. No inventes ofertes noves."""

SYSTEM_PROMPT_FILTRAR = """Ets un conseller d'ocupació. Rebràs ofertes numerades i \
el perfil d'una persona candidata. Indica quines ofertes descartaries per \
incompatibles amb el perfil (per exemple, fora de la comarca que demana, o un \
lloc per al que no té experiència ni vol formar-se). \
Respon només amb JSON vàlid amb esta forma:
{"descartats": [2, 5]}
Si no en descartaries cap: {"descartats": []}"""


def find_latest(directory: str = "resultats") -> Path | None:
    """El fitxer de resultats més recent (csv o json) o None si no n'hi ha."""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        return None
    files = [f for f in directory_path.iterdir()
             if f.suffix in (".csv", ".json") and f.is_file()]
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def _simplificada(row: dict, index: int) -> dict:
    """Oferta plana resumida per al prompte, numerada des d'1."""
    return {
        "id": index + 1,
        "titol": row.get("titol", ""),
        "empresa": row.get("empresa", ""),
        "lloc": row.get("lloc", ""),
        "detalls": row.get("detalls", ""),
    }


def puntuar_ofertes(config: dict, model: str | None, ofertes: list[dict], perfil: str) -> list[dict]:
    """Puntua ofertes (files planes) amb el proveïdor d'IA.

    Torna files amb `puntuacio` i `motiu` sumats als camps originals,
    ordenades de més a menys puntuació. Llança IAError si el model no
    respon o el text tornat no és JSON vàlid.
    """
    assert ofertes, "puntuar_ofertes rep una llista buida"
    proveidor = ProveidorIA.from_config(config, model=model)
    simplified = [_simplificada(row, i) for i, row in enumerate(ofertes)]
    user_prompt = (
        "PERFIL DE LA PERSONA CANDIDATA:\n"
        f"{perfil or 'Cap perfil concret: puntua segons la generalitat de cada oferta.'}\n\n"
        f"OFERTES:\n{json.dumps(simplified, ensure_ascii=False)}"
    )
    content = proveidor.chat(SYSTEM_PROMPT_AVALUAR, user_prompt)
    data = extract_json(content)
    per_id = {score.get("id"): score for score in data.get("avaluacions", [])}
    files = []
    for index, offer in enumerate(ofertes):
        score = per_id.get(index + 1, {})
        files.append(
            {
                "puntuacio": score.get("puntuacio", "-"),
                "motiu": score.get("motiu", ""),
                "portal": offer.get("portal", ""),
                "titol": offer.get("titol", ""),
                "empresa": offer.get("empresa", ""),
                "lloc": offer.get("lloc", ""),
                "data": offer.get("data", ""),
                "url": offer.get("url", ""),
            }
        )
    files.sort(
        key=lambda r: r["puntuacio"] if isinstance(r["puntuacio"], (int, float)) else -1,
        reverse=True,
    )
    return files


def filtrar_ofertes(config: dict, model: str | None, ofertes: list[dict], criteri: str) -> list[dict]:
    """Torna les ofertes que la IA no descarta per al perfil."""
    assert ofertes, "filtrar_ofertes rep una llista buida"
    proveidor = ProveidorIA.from_config(config, model=model)
    simplified = [_simplificada(row, i) for i, row in enumerate(ofertes)]
    user_prompt = (
        f"PERFIL: {criteri or '(usa la generalitat)'}\n\n"
        f"OFERTES:\n{json.dumps(simplified, ensure_ascii=False)}"
    )
    content = proveidor.chat(SYSTEM_PROMPT_FILTRAR, user_prompt)
    data = extract_json(content)
    descartats = {int(i) for i in data.get("descartats", []) if str(i).isdigit()}
    return [row for i, row in enumerate(ofertes) if (i + 1) not in descartats]


def guardar_avaluades(rows: list, directory: str = "resultats") -> Path:
    """Escriu el rànquing a un CSV nou (mai sobreescriu: nom amb segell horari)."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"avaluades-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    fields = ["puntuacio", "motiu", "portal", "titol", "empresa", "lloc", "data", "url"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
    return path


def print_avaluades(rows: list) -> None:
    table = Table(box=None, header_style="bold", show_lines=False)
    table.add_column("Pts", justify="right", style="bold cyan", width=3)
    table.add_column("Títol", max_width=46)
    table.add_column("Empresa", max_width=22)
    table.add_column("Motiu", max_width=44)
    for row in rows:
        score = row["puntuacio"]
        numeric = isinstance(score, (int, float))
        style = "green" if numeric and score >= 7 else ("yellow" if numeric and score >= 4 else "red")
        table.add_row(f"[{style}]{score}[/]", str(row["titol"]), row.get("empresa", ""), row.get("motiu", ""))
    console.print(table)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="buscafeina avalua",
        description="Puntua ofertes amb IA local segons el teu perfil.",
    )
    parser.add_argument("fitxer", nargs="?", help="CSV/JSON de resultats (per defecte el més recent)")
    parser.add_argument("-m", "--model", help="model d'IA (per defecte el del config)")
    parser.add_argument("-p", "--perfil", help="perfil del candidat/a (experiència, preferències…)")
    parser.add_argument("-d", "--directori", default="resultats", help="carpeta de resultats")
    parser.add_argument("--filtrar", action="store_true",
                        help="a més de puntuar, descarta les que no encaixen")
    parser.add_argument("--simulacio", action="store_true",
                        help="mostra què faria sense cridar la IA ni escriure fitxers")
    parser.add_argument("--llistar-accions", action="store_true",
                        help="mostra les accions del JSON disponibles per a avalua")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(sys.argv[1:] if argv is None else list(argv))

    if args.llistar_accions:
        from .accions import cargar_accions, ruta_accions

        data = cargar_accions()
        console.print(f"Accions de [bold]{ruta_accions()}[/] per a [bold]avalua[/]:")
        for entry in data["accions"]:
            if set(entry.get("comandos", [])) & {"avalua", "tot"}:
                marca = " [dim](necessita IA)[/]" if entry.get("requereix_ia") else ""
                console.print(f"  [bold]{entry['nom']}[/]{marca} — {entry['describe']}")
        return

    config = load_config()
    model = args.model or config.get("model_ia")
    perfil = args.perfil or config.get("perfil", "")

    path = Path(args.fitxer) if args.fitxer else find_latest(args.directori)
    if not path or not path.exists():
        console.print(
            "[red]No hi ha cap fitxer de resultats. Executa primer una cerca "
            "amb --guardar (p. ex. buscafeina cerca -k fuster -l València --guardar).[/]"
        )
        sys.exit(1)

    from .motor import llegir_ofertes

    ofertes = llegir_ofertes(path)
    if not ofertes:
        console.print(f"[yellow]El fitxer {path} no té ofertes reals a avaluar.[/]")
        sys.exit(0)

    if args.simulacio:
        proveidor = ProveidorIA.from_config(config, model=model)
        ok, motiu = proveidor.disponble()
        console.print(
            f"[bold]Simulació[/] de l'acció «avaluar-perfil» sobre [bold]{len(ofertes)}[/] "
            f"ofertes de [bold]{path.name}[/] amb [bold cyan]{proveidor.model}[/]:\n"
            "  1. Puntuació 0-10 i motiu breu per oferta.\n"
            f"  2. Rànquing ordenat i guardat a {args.directori}/avaluades-<data>.csv.\n"
            "  No s'ha cridat la IA ni s'ha escrit res.\n"
            f"  Proveïdor {'disponible' if ok else 'NO disponible'}: {motiu or 'ok'}"
        )
        return

    console.print(f"Avaluant [bold]{len(ofertes)}[/] ofertes de [bold]{path.name}[/]…")
    try:
        with console.status("El model està pensant (pot trigar uns minuts)…"):
            files = puntuar_ofertes(config, model, ofertes, perfil)
            if args.filtrar:
                files = filtrar_ofertes(config, model, files, perfil)
    except (IAError, BuscafeinaError) as error:
        console.print(f"[red]{error}[/]")
        sys.exit(error.exit_code)

    console.print()
    print_avaluades(files)
    saved = guardar_avaluades(files, directory=args.directori)
    console.print(f"\n[green]Resultats avaluats guardats a [bold]{saved}[/][/]")


if __name__ == "__main__":
    main()
