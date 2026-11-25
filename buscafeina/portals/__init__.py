"""Registre de portals de cerca de feina."""

from .infojobs import InfoJobs
from .labora import Labora
from .linkedin import LinkedIn
from .pacte import PacteComarcal
from .sepe import SEPE
from .turijobs import Turijobs

__all__ = ["PORTAL_CLASSES", "get_portal"]

# La clau coincideix amb els noms de PORTALS a options.py
PORTAL_CLASSES = {
    "Labora": Labora,
    "InfoJobs": InfoJobs,
    "Pacte Comarcal": PacteComarcal,
    "LinkedIn": LinkedIn,
    "SEPE": SEPE,
    "Turijobs": Turijobs,
}


def get_portal(name: str, criteria, config: dict):
    return PORTAL_CLASSES[name](criteria, config)
