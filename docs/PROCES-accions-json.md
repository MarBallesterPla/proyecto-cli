# Procés: accions predefinides en JSON extern

Aquesta documenta el treball fet a la branca `feature/acciones-json`.

## Problema

Al v1.0.0 l'ordre de les accions (cerca → avalua → exporta → neteja) estava
codificat dins del codi Python. Afegir, treure o reordenar una acció exigia
tocar codi i tornar a publicar.

## Decisió (ADR-001)

Moure la definició de les accions a `buscafeina/data/accions.json`, validat
amb `jsonschema` (`data/esquema-accions.json`). El codi només executa el que
l'JSON declara.

## Què canvia per a l'usuari/ària

- `buscafeina accions` mostra la taula d'accions disponibles.
- Cada acció té paràmetres amb `per_defecte` i `permesos`.
- Un JSON roto produeix un `ConfigError` llegible que assenyala l'element
  concret (`accions/0`), mai un traceback.

## Proves

`tests/test_accions.py` cobreix: càrrega correcte, validació d'esquema,
errors de lèxic i que la CLI no rebenta amb un JSON corrupte.
