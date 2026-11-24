"""Avaluació d'ofertes guardades amb un model local d'Ollama.

Ús:
    buscafeina avalua                          # avalua el fitxer més recent
    buscafeina avalua resultats/fitxer.csv     # avalua un fitxer concret
    buscafeina avalua -p "2 anys d'experiència en forneria" --model qwen3
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

from .config import load_config

console = Console()
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

SYSTEM_PROMPT = """Ets un conseller d'ocupació. Rebràs una llista d'ofertes de \
treball numerades i el perfil d'una persona candidata.
Per a cada oferta has de:
1. Puntuar de 0 a 10 l'adequació per a la persona candidata (10 = encaixa perfecta).
2. Donar un motiu breu en valencià (màxim 15 paraules).
Respon SEMPRE només amb JSON vàlid, sense markdown ni text extra, amb esta \
forma exacta:
{"avaluacions": [{"id": 1, "puntuacio": 7, "motiu": "exemple de motiu"}, \
{"id": 2, "puntuacio": 3, "motiu": "exemple de motiu"}]}
L'"id" ha de coincidir amb l'id de cada oferta. No inventes ofertes noves."""


def find_latest(directory: str = "resultats") -> Path | None:
    """El fitxer de resultats més recent (csv o json)."""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        return None
    files = [f for f in directory_path.iterdir()
             if f.suffix in (".csv", ".json") and f.is_file()]
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def load_offers(path: Path) -> list:
    """Llig un fitxer de resultats i torna les ofertes vàlides."""
    if path.suffix == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))
    else:  # csv
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
    offers = [
        row for row in rows
        if row.get("titol") and "(cerca al navegador)" not in row["titol"]
    ]
    return offers


def check_ollama(model: str) -> str | None:
    """Comprova el servidor i el model; torna un missatge d'error o None."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return (
            "No hi ha cap servidor Ollama al port 11434. "
            "Inicia Ollama (o executa 'ollama serve') i torna-ho a provar."
        )
    installed = [m.get("name", "") for m in response.json().get("models", [])]
    base_names = {name.split(":")[0] for name in installed}
    if model not in installed and model not in base_names:
        return (
            f"El model '{model}' no està descarregat. "
            f"Models disponibles: {', '.join(installed) or 'cap'}. "
            f"Baixa'l amb: ollama pull {model}"
        )
    return None


def avaluar(model: str, offers: list, perfil: str) -> list:
    """Envia totes les ofertes en una petició i torna les avaluacions."""
    simplified = [
        {
            "id": index + 1,
            "titol": row.get("titol", ""),
            "empresa": row.get("empresa", ""),
            "lloc": row.get("lloc", ""),
            "detalls": row.get("detalls", ""),
        }
        for index, row in enumerate(offers)
    ]
    perfil_text = (
        perfil
        or "Cap perfil concret: puntua segons la generalitat de cada oferta."
    )
    user_prompt = (
        f"PERFIL DE LA PERSONA CANDIDATA:\n{perfil_text}\n\n"
        f"OFERTES:\n{json.dumps(simplified, ensure_ascii=False)}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"temperature": 0.2},
    }
    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=900)
    if response.status_code == 400 and "think" in response.text.lower():
        payload.pop("think")  # models/versions sense suport de 'think'
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=900)
    response.raise_for_status()
    content = response.json()["message"]["content"]
    return _parse_avaluacions(content)


def _parse_avaluacions(content: str) -> list:
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise ValueError(f"El model no ha tornat JSON: {content[:200]}")
        data = json.loads(match.group())
    return data.get("avaluacions", [])


def print_avaluades(rows: list) -> None:
    table = Table(box=None, header_style="bold", show_lines=False)
    table.add_column("Pts", justify="right", style="bold cyan", width=3)
    table.add_column("Títol", max_width=46)
    table.add_column("Empresa", max_width=22)
    table.add_column("Motiu", max_width=44)
    for row in rows:
        score = row["puntuacio"]
        style = (
            "green" if score >= 7
            else "yellow" if score >= 4
            else "red"
        )
        table.add_row(
            f"[{style}]{score}[/]",
            row["titol"],
            row.get("empresa", ""),
            row.get("motiu", ""),
        )
    console.print(table)


def save_avaluades(rows: list, directory: str = "resultats") -> Path:
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"avaluades-{datetime.now().strftime('%Y%m%d-%H%M')}.csv"
    fields = ["puntuacio", "motiu", "portal", "titol", "empresa", "lloc", "data", "url"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(
            {key: row.get(key, "") for key in fields} for row in rows
        )
    return path


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="buscafeina avalua",
        description="Puntua les ofertes guardades amb un model local d'Ollama.",
    )
    parser.add_argument("fitxer", nargs="?", help="CSV/JSON de resultats (per defecte el més recent)")
    parser.add_argument("-m", "--model", help="model d'Ollama (per defecte el del config)")
    parser.add_argument("-p", "--perfil", help="perfil del candidat (experiència, preferències…)")
    parser.add_argument("-d", "--directori", default="resultats", help="carpeta de resultats")
    args = parser.parse_args(argv)

    config = load_config()
    model = args.model or config.get("model_ollama", "qwen3")
    perfil = args.perfil or config.get("perfil", "")

    path = Path(args.fitxer) if args.fitxer else find_latest(args.directori)
    if not path or not path.exists():
        console.print(
            "[red]No hi ha cap fitxer de resultats. Executa primer una cerca "
            "amb --guardar.[/]"
        )
        sys.exit(1)

    offers = load_offers(path)
    if not offers:
        console.print(f"[yellow]El fitxer {path} no té ofertes a avaluar.[/]")
        sys.exit(0)

    error = check_ollama(model)
    if error:
        console.print(f"[red]{error}[/]")
        sys.exit(1)

    console.print(
        f"Avaluant [bold]{len(offers)}[/] ofertes de [bold]{path.name}[/] amb "
        f"[bold cyan]{model}[/]…"
    )
    try:
        with console.status("El model està pensant (pot trigar uns minuts)…"):
            scores = avaluar(model, offers, perfil)
    except requests.RequestException as e:
        console.print(f"[red]Error de connexió amb Ollama: {e}[/]")
        sys.exit(1)
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        console.print(f"[red]Resposta inesperada del model: {e}[/]")
        sys.exit(1)

    by_id = {score.get("id"): score for score in scores}
    merged = []
    for index, offer in enumerate(offers):
        score = by_id.get(index + 1, {})
        merged.append(
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
    merged.sort(key=lambda r: r["puntuacio"] if isinstance(r["puntuacio"], (int, float)) else -1, reverse=True)

    console.print()
    print_avaluades(merged)
    saved = save_avaluades(merged)
    console.print(f"\n[green]Resultats avaluats guardats a [bold]{saved}[/][/]")


if __name__ == "__main__":
    main()
