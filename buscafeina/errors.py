"""Excepcions pròpies de buscafeina.

Totes derivan de BuscafeinaError, que els punts d'entrada (cli.main i
cli.avalua_main) converteixen en un missatge legible per a l'usuari/ària i
un codi de sortida no nul, mai en un traceback.
"""


class BuscafeinaError(Exception):
    """Error previsible: es mostra com a missatge, mai com a traceback."""

    #: codi de sortida del procés quan es produeix este error
    exit_code = 1


class ConfigError(BuscafeinaError):
    """Configuració externa invàlida o malformada (config.json, accions.json)."""

    exit_code = 2


class AccioNoValida(BuscafeinaError):
    """Es demana una acció que no existeix o no està permesa a accions.json."""

    exit_code = 2


class IAError(BuscafeinaError):
    """La capa d'IA no pot respondre (sense servidor, sense model, sense clau)."""

    exit_code = 3
