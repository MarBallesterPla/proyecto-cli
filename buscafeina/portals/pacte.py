"""Portal Pacte Comarcal per a l'Ocupació.

Cada comarca té el seu propi pacte i borsa d'ocupació; no hi ha un
cercador unificat. La URL és configurable a ~/.buscafeina/config.json
(clau "pacte_comarcal_url").
"""

from .base import Portal


class PacteComarcal(Portal):
    id = "pacte"
    label = "Pacte Comarcal"
    browser_only = True
    note = (
        "El portal del pacte comarcal no té cercador públic: configura la "
        "URL de la teua comarca a ~/.buscafeina/config.json "
        "(clau \"pacte_comarcal_url\")."
    )

    def browser_url(self) -> str:
        return self.config.get(
            "pacte_comarcal_url",
            "https://avalemterritori.es/acords-territorials/pactes-per-locupacio/",
        )
