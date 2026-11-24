"""Portal InfoJobs (infojobs.net).

Dos modes de lectura:
1. API oficial (si hi ha INFOJOBS_CLIENT_ID i INFOJOBS_CLIENT_SECRET a
   l'entorn; clau gratuïta a https://developer.infojobs.net).
2. Rascat de la pàgina de resultats (HTML SSR).

Si res no funciona, el CLI ofereix obrir la cerca al navegador.
"""

import base64
import os
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from ..models import Offer
from ..options import INFOJOBS_CONTRACT, INFOJOBS_WORKDAY
from .base import Portal, PortalError, http_get, slugify

BASE_URL = "https://www.infojobs.net"
API_URL = "https://api.infojobs.net/api/9/offer"


class InfoJobs(Portal):
    id = "infojobs"
    label = "InfoJobs"
    note = (
        "InfoJobs està bloquejant la lectura automàtica ara mateix: obri la "
        "cerca al navegador, o configura INFOJOBS_CLIENT_ID/INFOJOBS_CLIENT_SECRET."
    )

    def browser_url(self) -> str:
        terms = self.criteria.keyword_terms()
        locality = self.criteria.locality.strip()
        url = f"{BASE_URL}/ofertas-trabajo"
        params = {}
        if terms:
            params["keyword"] = terms
        if locality:
            params["where"] = locality
        if params:
            query = "&".join(
                f"{k}={quote_plus(v)}" for k, v in params.items()
            )
            url = f"{url}?{query}"
        return url

    def has_api_credentials(self) -> bool:
        return bool(
            os.environ.get("INFOJOBS_CLIENT_ID")
            and os.environ.get("INFOJOBS_CLIENT_SECRET")
        )

    def fetch_offers(self, limit: int = 10) -> list:
        if self.has_api_credentials():
            try:
                return self._fetch_api(limit)
            except Exception:
                pass  # caiguda al rascat
        return self._fetch_html(limit)

    # --- API oficial ---------------------------------------------------

    def _fetch_api(self, limit: int) -> list:
        credentials = base64.b64encode(
            f"{os.environ['INFOJOBS_CLIENT_ID']}"
            f":{os.environ['INFOJOBS_CLIENT_SECRET']}".encode()
        ).decode()

        params = {
            "q": self.criteria.keyword_terms(),
            "maxResults": str(limit),
            "order": "relevancia-desc",
        }
        if self.criteria.locality.strip():
            params["city"] = slugify(self.criteria.locality)
        contract = INFOJOBS_CONTRACT.get(self.criteria.contract)
        if contract:
            params["contractType"] = contract
        workday = INFOJOBS_WORKDAY.get(self.criteria.workday)
        if workday:
            params["workday"] = workday

        response = http_get(
            API_URL, headers={"Authorization": f"Basic {credentials}"}, params=params
        )
        if response.status_code != 200:
            raise PortalError(f"InfoJobs API: HTTP {response.status_code}")
        offers = []
        for item in response.json().get("offers", []):
            offers.append(
                Offer(
                    title=item.get("title", ""),
                    company=(item.get("author") or {}).get("name", ""),
                    location=item.get("city", ""),
                    url=item.get("link", ""),
                    date=(item.get("published") or "")[:10],
                    extra=" · ".join(
                        part
                        for part in (
                            (item.get("contractType") or {}).get("name", ""),
                            (item.get("workDay") or {}).get("name", ""),
                        )
                        if part
                    ),
                )
            )
        return offers[:limit]

    # --- Rascat de la pàgina SSR ----------------------------------------

    MAX_PAGES = 3

    def _fetch_html(self, limit: int) -> list:
        """Rasca fins a MAX_PAGES pàgines i filtra per localitat en local.

        El filtre 'where' d'InfoJobs l'aplica el seu JavaScript al
        navegador, no el servidor, així que cal filtrar ací.
        """
        collected: list = []
        seen: set = set()
        for page in range(1, self.MAX_PAGES + 1):
            try:
                separator = "&" if "?" in self.browser_url() else "?"
                response = http_get(f"{self.browser_url()}{separator}page={page}")
            except Exception:
                break  # pàgina bloquejada o inexistent: usem el que tinguem
            offers = self._parse_offers(response.text)
            if not offers:
                break
            for offer in offers:
                key = (offer.title, offer.url)
                if key not in seen:
                    seen.add(key)
                    collected.append(offer)
            if len(collected) >= limit * 3:
                break  # prou per a filtrar i truncar
        collected = self._filter_by_locality(collected)
        return collected[:limit]

    def _parse_offers(self, html: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        offers = []
        for card in soup.select("li.ij-OfferList-offerCardItem"):
            link = card.select_one('a[href*="/of-i"]') or card.select_one("h2 a, h3 a")
            title = _clean(link.get_text()) if link else ""
            if not title:
                heading = card.find(["h2", "h3"])
                title = _clean(heading.get_text()) if heading else ""
            if not title:
                continue
            href = ""
            if link and link.has_attr("href"):
                href = urljoin(BASE_URL, link["href"])
            company_tag = card.select_one("h4")
            details = [
                _clean(li.get_text())
                for li in card.select(
                    "li[class*='description-list-item']"
                )
            ]
            offers.append(
                Offer(
                    title=title,
                    url=href,
                    company=_clean(company_tag.get_text()) if company_tag else "",
                    extra=" · ".join(d for d in details if d),
                )
            )
        return offers

    def _filter_by_locality(self, offers: list) -> list:
        """El filtre 'where' l'aplica el navegador; aquí el fem a mano.

        Filtra per la localitat; si cap oferta hi coincidix, es mostren
        totes (millor veure'n que no pas no veure res).
        """
        locality = slugify(self.criteria.locality) if self.criteria.locality else ""
        if not locality:
            return offers
        matching = [
            offer
            for offer in offers
            if locality in slugify(f"{offer.extra} {offer.title}")
        ]
        return matching if matching else offers

    def post_fetch_note(self, offers: list) -> str:
        if self.criteria.locality and not self.has_api_credentials():
            return (
                "Nota: sense API, InfoJobs no permet aplicar la localitat a la "
                "lectura automàtica; al navegador sí que s'hi aplica."
            )
        return None


def _clean(text: str) -> str:
    return " ".join(text.split())
