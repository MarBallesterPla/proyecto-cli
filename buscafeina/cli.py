"""Interfície de buscafeina: argparse, prompts i eixida bonica.

Esta capa no fa lògica de negoci: llegeix arguments, pregunta el que
calga, crida el motor (`motor.py`) o la seqüència d'accions (`acciones.py`)
i printa el resultat. Tots els errors previsibles (ConfigError,
AccioNoValida, IAError, portal caigut, ruta inexistent) es converteixen ací
en missatges legibles amb codi de sortida no nul — mai un traceback.

Subcomandaments:

    buscafeina cerca    [opcions]      busca als portals i aplica les accions del JSON
    buscafeina tot      [opcions]      cerca + exporta + avalua en una passada
    buscafeina avalua   [fitxer]       puntua ofertes amb IA
    buscafeina neteja   [opcions]      accions destructives (confirmades o simulades)
    buscafeina accions                 llista les accions de accions.json i l'esquema
"""

import argparse
import sys

from rich.console import Console

from .accions import accio_anomenada, accions_per_comando, cargar_accions, ruta_accions
from .avalua import main as main_avalua
from .config import CONFIG_PATH, load_config, load_dotenv
from .errors import AccioNoValida, BuscafeinaError, ConfigError, IAError
from .models import Criteria
from .options import (
    CONTRACT_OPTIONS,
    PORTALS,
    SCHEDULE_OPTIONS,
    SHIFT_OPTIONS,
    WORKDAY_OPTIONS,
)

console = Console()


# ------------------------------------------------------------- arguments

def _criteris_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, add_help=False)
    parser.add_argument("-k", "--keyword", help="tipus de treball (p. ex. 'cambrer/a')")
    parser.add_argument("-l", "--localitat", help="localitat o província")
    parser.add_argument("--contracte", choices=CONTRACT_OPTIONS, help="tipus de contracte")
    parser.add_argument("--jornada", choices=WORKDAY_OPTIONS, help="tipus de jornada")
    parser.add_argument("--torn", choices=SHIFT_OPTIONS, help="tipus de torn")
    parser.add_argument("--horari", choices=SCHEDULE_OPTIONS, help="tipus d'horari")
    parser.add_argument(
        "--portals", help="portals separats per comes (Labora,InfoJobs,Pacte Comarcal,LinkedIn)"
    )
    parser.add_argument("--limit", type=int, help="resultats per cercador")
    parser.add_argument("--model", help="model d'IA (si no, el del config)")
    parser.add_argument("-p", "--perfil", help="perfil per a les accions amb IA")
    parser.add_argument("--guardar", nargs="?", const="ambdos",
                        choices=["csv", "json", "ambdos", "no"],
                        help="guardar els resultats (csv, json, ambdos o no)")
    parser.add_argument("--no-browser", action="store_true",
                        help="no obrir el navegador: només mostra les URLs")
    parser.add_argument("--simulacio", action="store_true",
                        help="mostra què farien les accions sense cridar la IA ni escriure res")
    parser.add_argument("--si", action="store_true",
                        help="confirma les accions destructives sense preguntar")
    parser.add_argument("--exec", metavar="ACCIO", dest="exec",
                        help="executa només l'acció amb este nom (veure `buscafeina accions`)")
    return parser


def _neteja_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, add_help=False)
    parser.add_argument("--dies", type=int, help="edat màxima dels fitxers a esborrar (per defecte 30)")
    parser.add_argument("-d", "--directori", help="carpeta de resultats")
    parser.add_argument("--simulacio", action="store_true",
                        help="mostra què esborraria, sense esborrar res")
    parser.add_argument("--si", action="store_true",
                        help="confirma les accions destructives sense preguntar")
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buscafeina",
        description="Cerca, avalua i ordena ofertes de feina (Labora/SEPE/InfoJobs/"
                    "Turijobs/Pacte/LinkedIn).",
    )
    sub = parser.add_subparsers(dest="comando")
    sub.add_parser("cerca", parents=[_criteris_parser("cerca")], help="buscar ofertes als portals")
    sub.add_parser("tot", parents=[_criteris_parser("tot")],
                   help="cerca + exporta + avalua en una sola passada")

    neteja = _neteja_parser("neteja")
    sub.add_parser("neteja", parents=[neteja], help="esborrar fitxers vells")
    sub.add_parser("accions", help="llistar les accions definides a accions.json")
    return parser


def _avalia_argv(argv: list[str]) -> list[str]:
    """Els arguments del subcomandament avalua (tot el que ve darrere de 'avalua')."""
    return argv[argv.index("avalua") + 1:]


def parse_args(argv=None):
    """Interpreta argv i torna (comando, args). `buscafeina -k …` compte com a `cerca`."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "avalua":
        return "avalua", _avalia_argv(argv)
    if not argv or argv[0].startswith("-"):
        argv = ["cerca", *argv]
    args = build_parser().parse_args(argv)
    return args.comando, args


# ---------------------------------------------------------------- context

def _portals_triat(args) -> list:
    """Valida els portals indicats i torna els noms canònics (missatge humà si no)."""
    caps = {p.lower(): p for p in PORTALS}
    if getattr(args, "portals", None):
        triats, invalids = [], []
        for pieza in args.portals.split(","):
            pieza = pieza.strip()
            if not pieza:
                continue
            if pieza.lower() in caps:
                triats.append(caps[pieza.lower()])
            else:
                invalids.append(pieza)
        if invalids:
            raise AccioNoValida(
                f"Portals desconeguts: {', '.join(invalids)}. Permesos: {', '.join(PORTALS)}."
            )
        return triats
    return list(PORTALS)


def _ctx_from(args, config) -> dict:
    """Contexte compartit per totes les accions d'una executada."""
    guardar = getattr(args, "guardar", None)
    if guardar == "no":
        formats = []
    elif guardar:
        formats = {"csv": ["csv"], "json": ["json"]}.get(guardar, ["csv", "json"])
    else:
        formats = None  # les accions decidiran (per defecte csv + json)
    return {
        "config": config,
        "criteris": Criteria(
            keyword=(getattr(args, "keyword", "") or "").strip(),
            locality=(getattr(args, "localitat", "") or "").strip(),
            contract=getattr(args, "contracte", None) or "Qualsevol",
            workday=getattr(args, "jornada", None) or "Qualsevol",
            shift=getattr(args, "torn", None) or "Qualsevol",
            schedule=getattr(args, "horari", None) or "Qualsevol",
        ),
        "portals": _portals_triat(args),
        "limit": getattr(args, "limit", None) or int(config.get("resultats_per_cercador", 10)),
        "model": getattr(args, "model", None),
        "perfil": getattr(args, "perfil", None) or config.get("perfil", ""),
        "directori": getattr(args, "directori", None) or config.get("directori_resultats", "resultats"),
        "formats": formats,
        "fitxers": [],
        "avisos": [],
    }


def _ctx_neteja(args, config) -> dict:
    return {
        "config": config,
        "criteris": Criteria(),
        "portals": [],
        "limit": 0,
        "model": None,
        "perfil": "",
        "directori": getattr(args, "directori", None) or config.get("directori_resultats", "resultats"),
        "formats": [],
        "fitxers": [],
        "avisos": [],
    }


# ------------------------------------------------------------------ eixida

def _mostra_ctx(ctx: dict) -> None:
    from rich.panel import Panel
    from rich.table import Table

    c = ctx["criteris"]
    taula = Table(show_header=False, box=None, pad_edge=False)
    taula.add_column(style="bold")
    taula.add_column()
    taula.add_row("Tipus de treball", c.keyword or "—")
    taula.add_row("Localitat", c.locality or "—")
    taula.add_row("Contracte", c.contract)
    taula.add_row("Jornada", c.workday)
    taula.add_row("Torn", c.shift)
    taula.add_row("Horari", c.schedule)
    taula.add_row("Portals", ", ".join(ctx["portals"]) or "—")
    taula.add_row("Límit", str(ctx["limit"]))
    console.print(Panel(taula, title="Resum de la cerca", border_style="cyan"))


def _mostra_ofertes(parells: list) -> None:
    from rich.table import Table

    for portal, ofertes in parells:
        color = "green" if ofertes else "yellow"
        console.rule(f"[{color}]{portal.label}[/{color}]")
        if not ofertes:
            console.print(f"  [yellow]{portal.note}[/]")
            console.print(f"  [dim]URL de cerca: {portal.browser_url()}[/]")
            continue
        taula = Table(box=None, header_style="bold")
        taula.add_column("Títol", max_width=52)
        taula.add_column("Empresa", max_width=24)
        taula.add_column("Lloc", max_width=26)
        taula.add_column("Detalls", max_width=34)
        for offer in ofertes:
            títol = f"[link={offer.url}]{offer.title}[/]" if offer.url else offer.title
            taula.add_row(títol, offer.company, offer.location, offer.extra)
        console.print(taula)


def _llistar_accions(comando: str | None = None) -> None:
    """`buscafeina accions` — la ruta del JSON, l'esquema i què fa cada acció."""
    from rich.table import Table

    data = cargar_accions()
    console.print(f"Fitxer carregat: [bold]{ruta_accions()}[/]")
    console.print("Esquema: [bold]buscafeina/data/esquema-accions.json[/] "
                  "(valida abans d'executar; si falla, diu quin camp)\n")
    taula = Table(header_style="bold")
    taula.add_column("Acció", style="bold cyan")
    taula.add_column("Efecte")
    taula.add_column("Comandos")
    taula.add_column("IA")
    taula.add_column("Destructiva")
    taula.add_column("Simulable")
    taula.add_column("Descripció", max_width=40)
    for e in data["accions"]:
        if comando and not (set(e.get("comandos", [])) & {comando, "tot"}):
            continue
        taula.add_row(
            e["nom"], e["efecte"], ", ".join(e["comandos"]),
            "sí" if e.get("requereix_ia") else "—",
            "sí" if e.get("destructiva") else "—",
            "sí" if e.get("simulable", True) else "—",
            e["describe"],
        )
    console.print(taula)


# ------------------------------------------------------------ repartidor

def _seqüència(data: dict, comando: str, args) -> list:
    """Les accions a executar, en ordre, resolt `--exec` i expandida `despres`.

    Les accions són combinables: si una declara `despres`, eixa s'encadena a
    continuació (les repetides només van una volta).
    """
    if getattr(args, "exec", None):
        return [accio_anomenada(data, comando, args.exec)]
    disponibles = accions_per_comando(data, comando)
    per_nom = {a.nom: a for a in disponibles}
    eixida, vists = [], set()
    for accio in disponibles:
        cua = [accio]
        while cua:
            actual = cua.pop(0)
            if actual.nom in vists:
                continue
            vists.add(actual.nom)
            eixida.append(actual)
            for següent in actual.despres:
                if següent in per_nom and per_nom[següent].nom not in vists:
                    cua.append(per_nom[següent])
    return eixida


def _executa(comando: str, args, config) -> None:
    data = cargar_accions()
    aplicats = 0
    ctx = _ctx_neteja(args, config) if comando == "neteja" else _ctx_from(args, config)

    if comando in ("cerca", "tot"):
        console.print()
        _mostra_ctx(ctx)
        console.print()

    if ctx.get("formats") is not None:
        # l'usuari ha dit què guardar: ho propagem a l'acció d'exportar
        for entrada in data["accions"]:
            if entrada["nom"] == "exportar-fitxers":
                entrada.setdefault("params", {})["formats"] = {"per_defecte": ctx["formats"]}
    if comando == "neteja" and getattr(args, "dies", None):
        for entrada in data["accions"]:
            if entrada["nom"] == "neteja-vells":
                entrada.setdefault("params", {})["dies"] = {"per_defecte": args.dies}

    simulacio = bool(getattr(args, "simulacio", False))
    confirmat = bool(getattr(args, "si", False))
    for accio in _seqüència(data, comando, args):
        missatge = accio.executar(ctx, simulacio=simulacio, confirmat=confirmat, consola=console)
        console.print(missatge)
        aplicats += 1
        if accio.efecte == "cerca" and not simulacio:
            _mostra_ofertes(ctx.get("parells", []))
            if not getattr(args, "no_browser", False):
                _obrir_pendents(ctx.get("parells", []))
        if accio.efecte in ("exportar", "avaluar") and ctx.get("fitxers") and not simulacio:
            for f in ctx["fitxers"][-1:]:
                console.print(f"  [green]fitxer escrit:[/] [bold]{f}[/]")
    for avís in ctx["avisos"]:
        console.print(f"  [yellow]Avís:[/] {avís}")
    if not aplicats:
        raise AccioNoValida(
            f"Cap acció del fitxer d'accions s'aplica al comando «{comando}». "
            "Executa `buscafeina accions` per a veure-les."
        )


def _obrir_pendents(parells: list) -> None:
    """Obri al navegador els portals sense lectura automàtica (o sense resultats).

    Si el navegador no arrenca, les URLs ja estan impreses: no es perd res.
    """
    import webbrowser

    pendents = [(p, o) for p, o in parells if not o]
    if not pendents:
        return
    console.print("\n[dim]Portals que requereixen navegador:[/]")
    for portal, _ in pendents:
        url = portal.browser_url()
        console.print(f"  [bold]{portal.label}[/] → {url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass


# ------------------------------------------------------------------ main

def main(argv=None) -> None:
    load_dotenv()
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        comando, args = parse_args(argv)
        if comando == "accions":
            _llistar_accions()
            return
        if comando == "avalua":
            main_avalua(args)  # args és la llista de paràmetres de `avalua`
            return
        config = load_config()
        _executa(comando, args, config)
    except (ConfigError, AccioNoValida, IAError, BuscafeinaError) as error:
        console.print(f"[red]{error}[/]")
        sys.exit(error.exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interromput per l'usuari/ària.[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()
