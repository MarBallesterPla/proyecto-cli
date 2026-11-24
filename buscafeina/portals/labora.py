"""Portal Labora - Servei Valencià d'Ocupació i Formació (GVA).

El cercador de Punt Labora (puntlabora.gva.es/consoferta/consulta) és un
formulari en diversos passos amb sessió pròpia: no es pot consultar
automàticament sense credencials (DNI + PIN). Per tant, aquest portal és
només de navegador: el CLI t'hi duu amb els criteris apuntats.
"""

from .base import Portal

SEARCH_URL = "https://puntlabora.gva.es/consoferta/consulta"


class Labora(Portal):
    id = "labora"
    label = "Labora"
    browser_only = True
    note = (
        "Punt Labora fa servir un formulari amb sessió (DNI/PIN): "
        "emplena-hi Ocupació, Província i els filtres de jornada manualment."
    )

    def browser_url(self) -> str:
        return SEARCH_URL
