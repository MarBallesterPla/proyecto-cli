"""Exportació dels resultats de la cerca a fitxers (CSV i JSON)."""

import csv
import json
from datetime import datetime
from pathlib import Path

from .portals.base import slugify

FIELDS = ["portal", "titol", "empresa", "lloc", "data", "detalls", "url"]

# separat ' ' perquè Excel en català/castellà l'obri correctament
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8-sig"


def _rows(portals_results) -> list:
    """Converteix (portal, ofertes) en files planes per a CSV/JSON."""
    rows = []
    for portal, offers in portals_results:
        if offers:
            for offer in offers:
                rows.append(
                    {
                        "portal": portal.label,
                        "titol": offer.title,
                        "empresa": offer.company,
                        "lloc": offer.location,
                        "data": offer.date,
                        "detalls": offer.extra,
                        "url": offer.url,
                    }
                )
        else:
            # portals sense lectura automàtica: guardem la URL de cerca
            rows.append(
                {
                    "portal": portal.label,
                    "titol": "(cerca al navegador)",
                    "empresa": "",
                    "lloc": "",
                    "data": "",
                    "detalls": portal.note or "",
                    "url": portal.browser_url(),
                }
            )
    return rows


def default_stem(criteria) -> str:
    """Nom base del fitxer: feina-panadero-valencia-20261110-103245 (amb segons)."""
    parts = ["feina"]
    if criteria.keyword:
        parts.append(slugify(criteria.keyword))
    if criteria.locality:
        parts.append(slugify(criteria.locality))
    # segons inclosos: dues cerques en el minut no es pisen
    parts.append(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return "-".join(parts)


def save_results(portals_results, criteria, formats: list, directory: str = "resultats") -> list:
    """Guarda els resultats i torna la llista de fitxers creats."""
    rows = _rows(portals_results)
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = default_stem(criteria)

    created = []
    for fmt in formats:
        path = out_dir / f"{stem}.{fmt}"
        if fmt == "csv":
            with open(path, "w", newline="", encoding=CSV_ENCODING) as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=CSV_DELIMITER)
                writer.writeheader()
                writer.writerows(rows)
        else:  # json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
        created.append(path)
    return created
