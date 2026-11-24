# ADR-001: Les accions predefinides viuen en `accions.json`, no en codi

- **Data**: 2026-11-24
- **Estat**: Acceptat

## Context

buscafeina executa "accions predefinides":seqüències d'operacions sobre els
portals i els fitxers de resultats (cercar, exportar, avaluar amb IA, netejar
fitxers vells…). La pregunta de disseny és on declarar eixes accions: dins de
Python (funcions o dictaris hardcoded) o en un fitxer de configuració extern
que l'usuari/ària pot editar.

## Decisió

Les accions es declaren en un fitxer JSON extern (`./accions.json`,
`~/.buscafeina/accions.json` o el que indique `BUSCAFEINA_ACCIONS`, amb un
fitxer d'exemple dins del paquet). El codi només conté les **classes
d'efecte** reutilitzables (`buscafeina/acciones.py`: cerca, exportar, avaluar,
filtrar, neteja, moure) i una fàbrica `Accio.from_config()` que construeix
cada acció des de la seua entrada JSON validada per esquema
(`buscafeina/data/esquema-accions.json`).

## Conseqüències

**Positives**

- Afegir o reordenar una acció (o una combinació nova amb `despres`) no exigeix
  tocar codi ni reinstal·lar el paquet: n'hi ha prou amb editar el JSON.
- La validació amb esquema abans d'executar converteix un JSON mal escrit en un
  missatge que diu el camp exacte (`accions/0/efecte: 'palla' is not one of…`),
  mai en un traceback.
- El fitxer JSON és declaratiu i llegible: serveix de documentació de què fa la
  CLI, i l'usuari el pot adaptar al seu pacte comarcal o als seus portals.
- Provable: les proves carreguen JSONs sintètics en `tmp_path` sense dependre de
  l'estat del dispositiu.

**Negatives / riscs**

- Cal mantindre l'esquema sincronitzat amb les classes d'efecte (si s'afig un
  efecte nou, cal afigre'l a l'enum de l'esquema). Mitigació: la prova
  `test_esquema_accepta_el_fitxer_d_exemple` i l'error explícit d'efecte
  desconegut a `Accio.from_config()`.
- Un JSON no pot expressar lògica arbitrària (bucles, condicions). Acceptat:
  les combinacions es fan amb `despres` i paràmetres tipats; per a lògica
  noves, s'escriu una classe d'efecte — que és precisament el que ha de ser
  codi.

## Alternatives descartades

- **YAML/TOML**: llegible, però afiga una dependència d'anàlisi i el JSON ja
  validem amb jsonschema; `.env` ja cobreix els secrets.
- **Classes Python per acció hardcoded**: fàcil d'escriure, però cada canvi
  d'usuari exigeix tocar i reinstal·lar el codi, i no es pot validar contra
  esquema.
- **Plugins dinàmics (importar mòduls des del JSON)**: perill de seguretat
  (executar qualsevol codi d'un fitxer d'usuari) per a un benefici que ací no
  cal.
