"""Portal SEPE — Sistema Nacional de Empleo (sistemanacionalempleo.es).

El portal públic del Servei Públic d'Ocupació Estatal (SEPE) agrega les
ofertes dels serveis públics d'ocupació de totes les comunitats autònomes
(incloent-hi Labora per a la Comunitat Valenciana) i es pot consultar sense
sessió. El formulari està basat en sessió: cal demanar primer un `idFlujo`
i després fer POST amb els criteris.

Alternativa a Labora: el mateix contingut públic (les ofertes de Labora
ixen ací també), però sense necessitat de DNI/PIN per a consultar.
"""

import re

import requests
from bs4 import BeautifulSoup

from ..models import Offer
from .base import Portal, PortalError

BASE = "https://www.sistemanacionalempleo.es"
INICIO = f"{BASE}/OfertaDifusionWEB/busquedaOfertas.do?modo=inicio"
BUSCAR = f"{BASE}/OfertaDifusionWEB/busquedaOfertas.do?modo=continuar"

# Comunitat Valenciana en el selector del formulari
CV_CODE = "10"


class SEPE(Portal):
    id = "sepe"
    label = "SEPE"
    note = "Ofertes públiques de tots els serveis autonòmics d'ocupació (inclòs Labora)."

    def browser_url(self) -> str:
        return INICIO

    def fetch_offers(self, limit: int = 10) -> list:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
        )
        # pas 1: la pàgina inicial ens dona el token de sessió (idFlujo)
        inicio = session.get(INICIO, timeout=25)
        inicio.raise_for_status()
        id_flujo = self._id_flujo(inicio.text)
        respuesta = session.post(
            BUSCAR,
            data={
                "idFlujo": id_flujo,
                "palabraBusqueda": self.criteria.keyword_terms(),
                "sectorProfesional": "",
                "botonNavegacion": "Enviar",
            },
            timeout=25,
        )
        respuesta.raise_for_status()
        ofertes = self._parse(respuesta.text)
        return self._filtra_localitat(ofertes)[:limit]

    @staticmethod
    def _id_flujo(html: str) -> str:
        for inp in BeautifulSoup(html, "html.parser").select("input[name=idFlujo]"):
            if inp.has_attr("value"):
                return inp["value"]
        raise PortalError("SEPE: el formulari no exposa el token de sessió (idFlujo) esperat.")

    @staticmethod
    def _parse(html: str) -> list:
        """Les files del tauler són (data, oferta, ubicació, detalls)."""
        ofertes = []
        for tr in BeautifulSoup(html, "html.parser").select("table tr"):
            cels = [" ".join(td.get_text(" ").split()) for td in tr.select("td")]
            if len(cels) >= 3 and re.match(r"\d{2}/\d{2}/\d{4}", cels[0]):
                ofertes.append(
                    Offer(
                        title=cels[1],
                        location=cels[2],
                        date=cels[0],  # dd/mm/aaaa, com el mostra el portal
                        extra=" · ".join(c for c in cels[3:] if c)[:60],
                    )
                )
        return ofertes

    def _filtra_localitat(self, ofertes: list) -> list:
        """Si l'usuari demana localitat, ens quedem amb les que la contenen."""
        text = (self.criteria.locality or "").strip()
        if not text:
            return ofertes
        bases = {w for w in re.split(r"[\s,/-]+", text.lower()) if len(w) > 3}
        matching = [
            o for o in ofertes
            if any(b in (o.location or "").lower() for b in bases)
        ]
        return matching if matching else ofertes

    def post_fetch_note(self, offers: list) -> str:
        if offers:
            return (
                "Nota: el SEPE agrega ofertes de tots els serveis autonòmics, "
                "inclòs Labora; per a postular-se cal demandant d'ocupació."
            )
        return None
