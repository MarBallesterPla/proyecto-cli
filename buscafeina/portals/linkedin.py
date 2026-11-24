"""Portal LinkedIn (linkedin.com/jobs).

Utilitza l'endpoint públic "jobs-guest" (el mateix que fa servir la web
sense sessió iniciada). Si LinkedIn el bloqueja, caiguda al navegador.
"""

from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from ..models import Offer
from ..options import LINKEDIN_CONTRACT, LINKEDIN_WORKDAY
from .base import Portal, http_get

GUEST_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
SEARCH_URL = "https://www.linkedin.com/jobs/search/"


class LinkedIn(Portal):
    id = "linkedin"
    label = "LinkedIn"

    def _params(self) -> dict:
        params = {
            "keywords": self.criteria.keyword_terms(),
            "location": self.criteria.locality.strip(),
        }
        # f_JT: F=complet, P=parcial, C=contracte, I=pràctiques, T=temporal, O=altres
        codes = {
            LINKEDIN_CONTRACT.get(self.criteria.contract),
            LINKEDIN_WORKDAY.get(self.criteria.workday),
        }
        codes.discard(None)
        if codes:
            params["f_JT"] = ",".join(sorted(codes))
        return {k: v for k, v in params.items() if v}

    def browser_url(self) -> str:
        query = "&".join(f"{k}={quote_plus(v)}" for k, v in self._params().items())
        return f"{SEARCH_URL}?{query}" if query else SEARCH_URL

    def fetch_offers(self, limit: int = 10) -> list:
        from urllib.parse import urlencode

        response = http_get(f"{GUEST_URL}?{urlencode(self._params())}&start=0")
        soup = BeautifulSoup(response.text, "html.parser")
        offers = []
        for card in soup.select("li div.base-search-card"):
            title_tag = card.select_one(".base-search-card__title")
            if title_tag is None:
                continue
            link_tag = card.select_one("a.base-card__full-link")
            company_tag = card.select_one(".base-search-card__subtitle")
            location_tag = card.select_one(".job-search-card__location")
            date_tag = card.select_one("time[datetime]")
            offers.append(
                Offer(
                    title=" ".join(title_tag.get_text().split()),
                    url=(link_tag["href"] if link_tag and link_tag.has_attr("href") else ""),
                    company=(
                        " ".join(company_tag.get_text().split()) if company_tag else ""
                    ),
                    location=(
                        " ".join(location_tag.get_text().split()) if location_tag else ""
                    ),
                    date=(date_tag["datetime"][:10] if date_tag else ""),
                )
            )
            if len(offers) >= limit:
                break
        return offers
