"""Models de dades de la CLI."""

from dataclasses import dataclass, field

from .options import SCHEDULE_TERMS, SHIFT_TERMS


@dataclass
class Criteria:
    """Criteris de cerca seleccionats per l'usuari/ària."""

    keyword: str = ""
    locality: str = ""
    contract: str = "Qualsevol"
    workday: str = "Qualsevol"
    shift: str = "Qualsevol"
    schedule: str = "Qualsevol"

    def keyword_terms(self) -> str:
        """Paraula clau completa: tipus de treball + torn + horari.

        Cap portal gran té filtre natiu de torn o horari, així que
        s'incorporen al text de la cerca.
        """
        terms = [self.keyword.strip()]
        if self.shift != "Qualsevol":
            terms.append(SHIFT_TERMS.get(self.shift, self.shift.lower()))
        if self.schedule != "Qualsevol":
            terms.append(SCHEDULE_TERMS.get(self.schedule, self.schedule.lower()))
        return " ".join(t for t in terms if t)


@dataclass
class Offer:
    """Una oferta de treball mostrada al terminal."""

    title: str
    url: str = ""
    company: str = ""
    location: str = ""
    date: str = ""
    extra: str = ""
