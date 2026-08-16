"""El piloto no se ensancha porque técnicamente se pueda."""

from config import MUNICIPIO_ALIAS, PILOTO_MUNICIPIOS, PILOTO_TERRITORIO, PILOTO_UNIVERSO, SECOP_WHERE
from modelo.constantes import MUNICIPIOS_ESPERADOS


def alcance_piloto() -> dict:
    return {
        "territorio": PILOTO_TERRITORIO,
        "municipios": PILOTO_MUNICIPIOS,
        "municipios_esperados": MUNICIPIOS_ESPERADOS,
        "universo": PILOTO_UNIVERSO,
        "consulta_ingesta": SECOP_WHERE,
        "escala": "piloto",
        "siguiente_escala": None,
        "nota": (
            "El alcance sigue siendo Antioquia. "
            "No se abre el país ni se pinta SECOP real en el mapa. "
            "Primero hay que ver si el contraste es útil."
        ),
        "alias_unicos": sorted(MUNICIPIO_ALIAS),
    }
