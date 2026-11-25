"""Proves dels portals nous (SEPE i Turijobs): parseig amb HTML fixt, sense xarxa.

Els HTML que s'analitzen són mostres reudes del viu (reduïdes), perquè la
prova verifique la selecció real i no una invenció. No es fa cap peticions:
el mètode de parseig és un mètode pur.
"""

from buscafeina.models import Criteria
from buscafeina.portals.sepe import SEPE
from buscafeina.portals.turijobs import Turijobs

HTML_SEPE = """
<table class="w100">
 <tr><td>25/11/2026</td><td>Camarero/a</td><td>Sopelana (Bizkaia)</td><td>Detalls</td></tr>
 <tr><td>24/11/2026</td><td>Cocinero/a</td><td>València (Valencia/València)</td><td></td></tr>
 <tr><td>Data</td><td>Descripción</td><td>Ubicación</td></tr>
 <tr><td>23/11/2026</td><td>Recepcionista</td><td>Gandia (Valencia/València)</td><td></td></tr>
</table>
"""

HTML_TURIJOBS = """
<div class="flex flex-col gap-4">
 <div class="flex gap-6 items-center w-full">
  <a href="https://www.turijobs.com/es/empresa/barcelo-hotel-group"><div><img/></div></a>
  <div><span title="Cocinero/a - Barceló Santiago">
   <a href="https://www.turijobs.com/es/oferta-trabajo/islas-canarias/cocineroa-barcelo-santiago/362609">
    <h2>Cocinero/a - Barceló Santiago</h2></a></span>
  </div>
 </div>
 <div class="flex flex-col gap-2">
  <a href="https://www.turijobs.com/es/empresa/barcelo-hotel-group"><div><span>Barceló Hotel Group</span></div></a>
  <a href="https://www.turijobs.com/es/ofertas-trabajo/valencia"><div><span>València, España</span></div></a>
  <div class="flex items-start"></div>
 </div>
</div>
"""


def test_sepe_parseja_files():
    """Camí feliç: files data/oferta/lloc → Offer amb la data del portal."""
    ofertes = SEPE._parse(HTML_SEPE)
    assert len(ofertes) == 3
    primera = ofertes[0]
    assert primera.title == "Camarero/a"
    assert primera.location == "Sopelana (Bizkaia)"
    assert primera.date == "25/11/2026"  # la data tal com la publica el SNE


def test_sepe_la_capcalera_no_es_confon_amb_oferta():
    """Cas felly: una fila de capçalera sense data no pot eixir com a oferta."""
    ofertes = SEPE._parse(HTML_SEPE)
    assert all(o.title != "Descripción" for o in ofertes)


def test_sepe_filtra_localitat():
    """Amb -l València, es queden les files de València i no les de Biscaia."""
    sepe = SEPE(Criteria(keyword="camarero", locality="València"), {})
    filtrades = sepe._filtra_localitat(SEPE._parse(HTML_SEPE))
    assert [o.title for o in filtrades] == ["Cocinero/a", "Recepcionista"]


def test_turijobs_meta_extreu_empresa_i_lloc():
    """Camí feliç: empresa de /es/empresa/ i ciutat de /es/ofertas-trabajo/."""
    from bs4 import BeautifulSoup

    cont = BeautifulSoup(HTML_TURIJOBS, "html.parser").div
    empresa, lloc = Turijobs._meta(cont)
    assert empresa == "Barceló Hotel Group"
    assert lloc == "València"  # sense «, España»


def test_turijobs_url_amble_localitat():
    """Camí feliç: la URL de navegador conté slug de paraula clau i província."""
    t = Turijobs(Criteria(keyword="cambrer/a", locality="València"), {})
    url = t.browser_url()
    assert url.startswith("https://www.turijobs.com/es/ofertas-trabajo/")
    assert "valencia" in url
