"""Flux principal de buscafeina."""

import argparse
import sys
import webbrowser

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import DEFAULTS, CONFIG_PATH, load_config
from .export import save_results
from .models import Criteria
from .options import (
    CONTRACT_OPTIONS,
    PORTALS,
    SCHEDULE_OPTIONS,
    SHIFT_OPTIONS,
    WORKDAY_OPTIONS,
)
from .portals import get_portal

console = Console()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="buscafeina",
        description="Busca feina a Labora, InfoJobs, Pacte Comarcal i LinkedIn.",
    )
    parser.add_argument("-k", "--keyword", help="tipus de treball (p. ex. 'cambrer/a')")
    parser.add_argument("-l", "--localitat", help="localitat o província")
    parser.add_argument("--contracte", choices=CONTRACT_OPTIONS, help="tipus de contracte")
    parser.add_argument("--jornada", choices=WORKDAY_OPTIONS, help="tipus de jornada")
    parser.add_argument("--torn", choices=SHIFT_OPTIONS, help="tipus de torn")
    parser.add_argument("--horari", choices=SCHEDULE_OPTIONS, help="tipus d'horari")
    parser.add_argument(
        "--portals", help="portals separats per comes (Labora,InfoJobs,Pacte Comarcal,LinkedIn)"
    )
    parser.add_argument("--limit", type=int, help="resultats per cercador (per defecte 10)")
    parser.add_argument(
        "--guardar",
        nargs="?",
        const="ambdos",
        choices=["csv", "json", "ambdos"],
        help="guardar els resultats en un fitxer (csv, json o ambdos)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="no obrir el navegador (mostra les URLs)"
    )
    return parser.parse_args(argv)


def _ask(build_prompt, default=None):
    """Construeix i executa un prompt; sense terminal interactiu, valor per defecte."""
    try:
        result = build_prompt().ask()
    except Exception:
        result = None
    if result is None:
        return default
    return result


def prompt_criteria(args) -> tuple[Criteria, list]:
    """Completa amb prompts interactius allò que no vinga dels arguments."""
    console.print(
        Panel.fit(
            "[bold cyan]buscafeina[/] · cerca feina a Labora, InfoJobs, "
            "Pacte Comarcal i LinkedIn",
            border_style="cyan",
        )
    )

    # Portals
    if args.portals:
        selected = [p.strip() for p in args.portals.split(",") if p.strip()]
        invalid = [p for p in selected if p not in PORTALS]
        if invalid:
            console.print(f"[red]Portals desconeguts: {', '.join(invalid)}[/]")
            sys.exit(2)
    else:
        selected = _ask(
            lambda: questionary.checkbox(
                "1/7 · En quins cercadors vols buscar?",
                choices=[questionary.Choice(p, checked=True) for p in PORTALS],
            ),
            default=PORTALS,
        )
        if not selected:
            console.print("[yellow]Cap portal seleccionat.[/]")
            sys.exit(0)

    keyword = args.keyword or _ask(
        lambda: questionary.text(
            "2/7 · Tipus de treball o paraula clau (p. ex. cambrer/a, dipositari…):"
        ),
        default="",
    )

    locality = args.localitat or _ask(
        lambda: questionary.text(
            "3/7 · Localitat o província (p. ex. València, Gandia…):"
        ),
        default="",
    )

    contract = args.contracte or _ask(
        lambda: questionary.select(
            "4/7 · Tipus de contracte:", choices=CONTRACT_OPTIONS
        ),
        default="Qualsevol",
    )

    workday = args.jornada or _ask(
        lambda: questionary.select("5/7 · Tipus de jornada:", choices=WORKDAY_OPTIONS),
        default="Qualsevol",
    )

    shift = args.torn or _ask(
        lambda: questionary.select(
            "6/7 · Tipus de torn (s'afegirà a la paraula clau):", choices=SHIFT_OPTIONS
        ),
        default="Qualsevol",
    )

    schedule = args.horari or _ask(
        lambda: questionary.select(
            "7/7 · Tipus d'horari (s'afegirà a la paraula clau):",
            choices=SCHEDULE_OPTIONS,
        ),
        default="Qualsevol",
    )

    criteria = Criteria(
        keyword=(keyword or "").strip(),
        locality=(locality or "").strip(),
        contract=contract,
        workday=workday,
        shift=shift,
        schedule=schedule,
    )
    return criteria, selected


def print_summary(criteria: Criteria) -> None:
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Tipus de treball", criteria.keyword or "—")
    table.add_row("Localitat", criteria.locality or "—")
    table.add_row("Contracte", criteria.contract)
    table.add_row("Jornada", criteria.workday)
    table.add_row("Torn", criteria.shift)
    table.add_row("Horari", criteria.schedule)
    if criteria.shift != "Qualsevol" or criteria.schedule != "Qualsevol":
        table.add_row(
            "[dim]Nota[/dim]",
            "[dim]torn i horari no tenen filtre natiu: s'incorporen a la "
            "paraula clau[/dim]",
        )
    console.print(Panel(table, title="Resum de la cerca", border_style="cyan"))


def print_offers(portal, offers) -> None:
    style = "green" if offers else "yellow"
    console.rule(f"[{style}]{portal.label}[/{style}]")
    if not offers:
        console.print(
            f"  [yellow]Sense lectura automàtica disponible."
            f"{(' ' + portal.note) if portal.note else ''}[/]"
        )
        return
    note = portal.post_fetch_note(offers)
    if note:
        console.print(f"  [dim]{note}[/]")
    table = Table(box=None, header_style="bold", show_lines=False)
    table.add_column("Títol", max_width=52)
    table.add_column("Empresa", max_width=24)
    table.add_column("Lloc", max_width=26)
    table.add_column("Data", max_width=10)
    table.add_column("Detalls", max_width=34)
    for offer in offers:
        title = (
            f"[link={offer.url}]{offer.title}[/]"
            if offer.url
            else offer.title
        )
        table.add_row(
            title,
            offer.company,
            offer.location,
            offer.date,
            offer.extra,
        )
    console.print(table)


def open_in_browser(portals, criteria, config, preselect) -> None:
    choices = [
        questionary.Choice(
            p.label,
            value=p,
            checked=p.id in preselect,
        )
        for p in portals
    ]
    to_open = _ask(
        lambda: questionary.checkbox(
            "Vols obrir les cerques al navegador? "
            "(espai per a marcar, enter per a continuar)",
            choices=choices,
        )
    )
    if to_open is None:
        show_urls(portals)  # terminal no interactiu: mostrem les URLs
        return
    for portal in to_open:
        url = portal.browser_url()
        console.print(f"  Obrint [link={url}]{portal.label}[/]…")
        webbrowser.open(url)


def show_urls(portals) -> None:
    console.print()
    for portal in portals:
        console.print(f"  [bold]{portal.label}[/]: {portal.browser_url()}")


def main(argv=None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "avalua":
        # subcomandament: buscafeina avalua [fitxer] [-p perfil] [-m model]
        from .avalua import main as avalua_main

        avalua_main(argv[1:])
        return
    args = parse_args(argv)
    config = load_config()
    criteria, selected_names = prompt_criteria(args)

    limit = args.limit or int(config.get("resultats_per_cercador", DEFAULTS["resultats_per_cercador"]))
    portals = [get_portal(name, criteria, config) for name in selected_names]

    console.print()
    print_summary(criteria)
    console.print()

    failed_ids = []
    portals_results = []
    for portal in portals:
        offers = []
        if not portal.browser_only:
            try:
                with console.status(f"Consultant {portal.label}…"):
                    offers = portal.fetch_offers(limit=limit)
            except Exception as error:
                console.print(f"  [red]Error consultant {portal.label}: {error}[/]")
        if portal.browser_only or not offers:
            failed_ids.append(portal.id)
        print_offers(portal, offers)
        portals_results.append((portal, offers))

    console.print()
    if args.no_browser:
        show_urls(portals)
    else:
        open_in_browser(portals, criteria, config, preselect=failed_ids)

    # Guardar els resultats
    mode = args.guardar
    if not mode:
        mode = _ask(
            lambda: questionary.select(
                "Vols guardar els resultats en un fitxer?",
                choices=["Ambdós", "CSV (Excel)", "JSON", "No"],
            ),
            default="No",
        )
        mode = {
            "Ambdós": "ambdos",
            "CSV (Excel)": "csv",
            "JSON": "json",
            "No": "no",
        }.get(mode, "no")
    if mode in ("csv", "json", "ambdos"):
        formats = ["csv", "json"] if mode == "ambdos" else [mode]
        try:
            created = save_results(portals_results, criteria, formats)
            for path in created:
                console.print(f"  Resultats guardats a [bold]{path}[/]")
        except OSError as error:
            console.print(f"  [red]No s'han pogut guardar: {error}[/]")

    console.print(
        f"\n[dim]Consell: la URL del teu Pacte Comarcal es configura a {CONFIG_PATH}[/]"
    )


if __name__ == "__main__":
    main()
