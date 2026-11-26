"""Proves de l'exportació de resultats: noms de fitxer i formats."""

import re

from buscafeina.export import default_stem
from buscafeina.models import Criteria


def test_default_stem_porta_segons():
    """El nom de l'export porta segons (HHMMSS): dues cerques en el minut no es pisen."""
    stem = default_stem(Criteria(keyword="panadero", locality="València"))
    parts = stem.split("-")
    assert parts[:3] == ["feina", "panadero", "valencia"]
    assert re.fullmatch(r"\d{8}", parts[-2])  # data AAAAMMDD
    assert re.fullmatch(r"\d{6}", parts[-1])  # hora HHMMSS, amb segons
