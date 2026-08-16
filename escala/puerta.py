"""No se escala solo porque técnicamente se pueda."""

from __future__ import annotations

from modelo.constantes import ESTADOS_REPORTE, ESTADOS_REPORTE_VISIBLES, MUNICIPIOS_ESPERADOS
from piloto.metricas import resumir_piloto

CRITERIOS = ("calidad", "utilidad", "trazabilidad", "moderacion")


def _calidad(datos: dict) -> tuple[bool, str]:
    n = len(datos.get("municipios") or {})
    if n != MUNICIPIOS_ESPERADOS:
        return False, f"el conjunto no cierra: hay {n} municipios, se esperan {MUNICIPIOS_ESPERADOS}"
    return True, "125 municipios de Antioquia con ceros visibles, no claves faltantes"


def _utilidad(resumen: dict) -> tuple[bool, str]:
    utiles = (resumen.get("metricas") or {}).get("reportes_utiles") or 0
    if utiles < 1:
        return False, "aún no hay un reporte útil al lado de un contrato"
    return True, f"{utiles} reporte(s) útil(es): hay contraste, no irregularidad"


def _trazabilidad(datos: dict) -> tuple[bool, str]:
    contratos = list((datos.get("contratos") or {}).values())
    if not contratos:
        return False, "no hay contratos para seguir hasta la fuente"
    sin_fuente = [c["id"] for c in contratos if not c.get("fuente")]
    if sin_fuente:
        return False, f"contratos sin fuente: {', '.join(sin_fuente)}"
    return True, "cada contrato del conjunto trae fuente; no se inventa la URL"


def _moderacion(datos: dict) -> tuple[bool, str]:
    if "DESCARTADO" not in ESTADOS_REPORTE or "VERIFICADO" not in ESTADOS_REPORTE:
        return False, "faltan estados de confianza"
    ocultos = [
        r
        for r in (datos.get("reportes") or {}).values()
        if r.get("estado") not in ESTADOS_REPORTE_VISIBLES
    ]
    if any(r.get("estado") not in ESTADOS_REPORTE for r in (datos.get("reportes") or {}).values()):
        return False, "hay un estado de reporte que el modelo no reconoce"
    return True, (
        "se puede explicar el estado; lo descartado no sale al mapa. "
        f"{len(ocultos)} fuera de la superficie pública"
    )


def evaluar_puerta(
    datos: dict,
    *,
    ruta_eventos=None,
    ruta_auditoria=None,
) -> dict:
    resumen = resumir_piloto(datos, ruta_eventos=ruta_eventos, ruta_auditoria=ruta_auditoria)
    chequeos = {
        "calidad": _calidad(datos),
        "utilidad": _utilidad(resumen),
        "trazabilidad": _trazabilidad(datos),
        "moderacion": _moderacion(datos),
    }
    detalle = {
        clave: {"ok": ok, "evidencia": evidencia} for clave, (ok, evidencia) in chequeos.items()
    }
    listos = all(item["ok"] for item in detalle.values())
    return {
        "criterios": CRITERIOS,
        "detalle": detalle,
        "listos": listos,
        "autorizacion": False,
        "puede_ensanchar": False,
        "regla": "Nunca escalar únicamente porque técnicamente es posible.",
        "lectura": (
            "La puerta de calidad, utilidad, trazabilidad y moderación está lista. "
            "Eso no autoriza a abrir el país ni a pintar SECOP en el mapa."
            if listos
            else "Falta demostrar alguno de los cuatro criterios. El mapa sigue en Antioquia."
        ),
    }
