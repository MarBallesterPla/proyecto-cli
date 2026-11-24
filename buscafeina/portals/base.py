"""Classe base dels portals de treball."""

import unicodedata
from abc import ABC, abstractmethod

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
TIMEOUT = 20


class PortalError(Exception):
    """No s'han pogut obtenir resultats d'un portal."""


def slugify(text: str) -> str:
    """'València' -> 'valencia', 'Sant Vicent del Raspeig' -> 'sant-vicent-del-raspeig'."""
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(c for c in normalized if not unicodedata.combining(c))
    words = "".join(c if c.isalnum() else " " for c in without_accents).split()
    return "-".join(words) if words else ""


def http_get(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("headers", {"User-Agent": USER_AGENT})
    kwargs.setdefault("timeout", TIMEOUT)
    response = requests.get(url, **kwargs)
    response.raise_for_status()
    return response


class Portal(ABC):
    """Un portal de cerca de feina.

    fetch_offers() intentarà mostrar resultats al terminal; si no és
    possible (bloqueig, sense endpoint públic...), retornarà [] i el CLI
    oferirà obrir browser_url() al navegador com a alternativa.
    """

    id: str = "portal"
    label: str = "Portal"
    # True si el portal no permet lectura automàtica (només navegador)
    browser_only: bool = False
    note: str = ""

    def __init__(self, criteria, config: dict):
        self.criteria = criteria
        self.config = config

    @abstractmethod
    def browser_url(self) -> str:
        """URL de cerca amb filtres per a obrir al navegador."""

    def fetch_offers(self, limit: int = 10) -> list:
        """Ofertes per al terminal (llista d'Offer), [] si no s'hi ha pogut."""
        return []

    def post_fetch_note(self, offers: list) -> str:
        """Avís a mostrar després de la lectura (o None si res a dir)."""
        return None
