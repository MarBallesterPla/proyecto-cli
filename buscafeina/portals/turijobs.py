"""Portal Turijobs (turijobs.com).

Portal líder d'ocupació del sector turisme i hosteleria, amb forta presència
a la Comunitat Valenciana. Les cerques es publiquen en URLs llegibles:

    https://www.turijobs.com/es/ofertas-trabajo/<slug-paraula-clau>
    https://www.turijobs.com/es/ofertas-trabajo/<slug>/<slug-provincia>

Sense clau ni sessió per a llegir-les.
"""

from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from ..models import Offer
from .base import Portal, http_get, slugify

BASE = "https://www.turijobs.com"


class Turijobs(Portal):
    id = "turijobs"
    label = "Turijobs"
    note = "Turisme i hosteleria d'Espanya (molta oferta de la CV)."

    def browser_url(self) -> str:
        slug = slugify(self.criteria.keyword_terms()) or "empleo"
        url = f"{BASE}/es/ofertas-trabajo/{quote_plus(slug)}"
        if self.criteria.locality:
            url += f"/{slugify(self.criteria.locality)}"
        return url

    def fetch_offers(self, limit: int = 10) -> list:
        response = http_get(self.browser_url())
        soup = BeautifulSoup(response.text, "html.parser")
        ofertes: list[Offer] = []
        vists: set[str] = set()
        for card in soup.select('a[href*="/oferta-trabajo/"]'):
            href = card["href"]
            if not href.startswith("http"):
                href = f"{BASE}{href}"
            titulo = " ".join(card.get_text(" ").split())
            if not titulo or href in vists:
                continue
            vists.add(href)
            empresa, lloc = self._meta(self._contenidor(card))
            ofertes.append(
                Offer(title=titulo, url=href, company=empresa, location=lloc)
            )
            if len(ofertes) >= limit:
                break
        return ofertes

    @staticmethod
    def _contenidor(card):
        """Puja des de l'enllaç fins al contenidor de la targeta sencera."""
        cont = card
        for _ in range(6):
            if cont is None:
                return None
            clases = " ".join(cont.get("class", []))
            if "flex-col" in clases and "gap-4" in clases:
                return cont
            cont = cont.parent
        return cont

    @staticmethod
    def _meta(cont) -> tuple[str, str]:
        """Extreu (empresa, lloc) dels enllaços d'empresa i ciutat.

        Estructura real (verificada sobre el HTML viu): dins del contenidor
        hi ha un enllaç a /es/empresa/<slug> amb el nom de l'empresa i un
        altre a /es/ofertas-trabajo/<slug> amb «Ciutat, País»; el slug de
        l'enllaç de ciutat no conté «oferta», així que el distingim bé.
        """
        if cont is None:
            return "", ""
        empresa = ""
        lloc = ""
        for link in cont.select('a[href*="/es/empresa/"]'):
            texto = " ".join(link.get_text(" ").split())
            if texto:
                empresa = texto
                break
        for link in cont.select('a[href*="/es/ofertas-trabajo/"]'):
            href = link.get("href", "")
            if "/oferta-trabajo/" in href:
                continue  # eixe és el títol de l'oferta, no la ciutat
            texto = " ".join(link.get_text(" ").split())
            if texto and "," in texto:
                lloc = texto.split(",")[0].strip()
                break
        return empresa, lloc
    def post_fetch_note(self, offers: list) -> str:
        return None
