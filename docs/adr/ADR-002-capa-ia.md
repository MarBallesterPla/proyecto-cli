# ADR-002: IA local (Ollama) per defecte, API compatible OpenAI opcional

- **Data**: 2026-11-24
- **Estat**: Acceptat

## Context

Dues accions (avaluar i filtrar ofertes) tenen sentit amb un model de
llenguatge. Les opcions eren: un servei de pagament amb clau, un model local,
o les dos.

## Decisió

Capa `buscafeina/ia.py` amb una interfície `ProveidorIA` i dos
implementacions: `Ollama` (per defecte, servidor local, sense clau i sense
eixida a internet) i `OpenAICompatible` (endpoint configurables; la clau es
llig exclusivament d'una variable d'entorn indicada a `openai_api_key_env`,
mai del codi ni del repositori). La elecció es fa a `config.json` amb
`proveidor_ia`, resolt per la fàbrica estàtica `ProveidorIA.from_config()`.

**Si el proveïdor no està disponible, la CLI no es trenca**: les accions amb
IA se salten amb un missatge que explica què falta (servidor parat, model no
descarregat amb la comanda per a baixar-lo, o variable d'entorn absent) i la
seqüència continua amb la resta d'accions. Així el modo sense red i sense Ollama
funciona: cerca, exportar, neteja i arxiu no depenen de l'IA.

## Conseqüències

- L'alumne/a pot treballar 100 % offline i sense claus (Ollama local), que era
  el requisit del projecte; qui tinga compte d'OpenAI o similar pot usar-lo
  canviant dos camps del config.
- Les proves substitueixen la fàbrica per un proveïdor simulat: cap test toca
  la xarxa.
- Risc: respostes no JSON dels models. Mitigats per `extract_json()` (tolera
  text al voltant, blocs de codi i tokens de raonament) que llança `IAError`
  llegible, i per la validació `format: json` de les dues APIs.

## Alternatives descartades

- **Ollama hardcoded al mòdul d'avaluació** (com en la versió inicial): barreja
  interfície i proveïdor; sense manera de canviar sense parchar codi.
- **Només OpenAI**: obligaria a tenir clau i xarxa, i filtraria dades de cerca
  de feina (perfil personal) a un servei de tercers.
