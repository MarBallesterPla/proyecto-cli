# Procés: capa IA desacoplada

Aquest document recull el treball fet a la branca `feature/capa-ia`.

## Problema

Al v1.0.0 la crida a Ollama estava enganxada al motor de cerca: si el model
no estava disponible, tota la cerca queia.

## Decisió (ADR-002)

Crear `buscafeina/ia.py` amb una interfície pròpia (`avaluar`, `explicar`)
i dos proveïdors intercanviables:

- **Ollama** local (per defecte).
- Qualsevol servidor compatible amb l'API d'OpenAI (`OPENAI_API_KEY` +
  `OPENAI_BASE_URL`).

La capa IA només es carrega quan es demana (`avalua` o `--avaluar`): una
cerca sense avaluar no toca cap servidor extern.

## Què canvia per a l'usuari/ària

- `buscafeina avalua -m <model>` puntua les ofertes de l'última cerca.
- Configuració via `.env` (veure `.env.example`) o variables d'entorn.
- Si el servidor IA no respon, missatge llegible i exit code 2, sense
  traceback.

## Proves

`tests/test_motor.py` (parseig de respostes i errors d'IA) i el proveïdor
simulat de `tests/conftest.py`: les proves corren sense servidor ni xarxa.
