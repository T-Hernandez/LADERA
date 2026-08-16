"""Consulta estructurada. La IA, si existe, solo llena esto. Nunca los resultados."""

from __future__ import annotations

from modelo.constantes import CATEGORIAS_REPORTE, ESTADOS_CONTRATO

CLAVES = (
    "territorio",
    "territorio_dane",
    "estado_contrato",
    "categoria_reporte",
    "periodo",
    "con_reportes",
    "con_relacion",
    "texto",
)


def consulta_vacia() -> dict:
    return {
        "territorio": None,
        "territorio_dane": None,
        "estado_contrato": None,
        "categoria_reporte": None,
        "periodo": None,
        "con_reportes": False,
        "con_relacion": False,
        "texto": None,
    }


def validar_consulta(crudo: dict) -> dict:
    """Rechaza claves que no sean filtros. La IA no puede colar ids ni respuestas."""
    if not isinstance(crudo, dict):
        raise ValueError("la interpretación tiene que ser un objeto")
    prohibidas = {"contratos", "reportes", "fuentes", "resultados", "ids", "respuesta"}
    for clave in crudo:
        if clave in prohibidas:
            raise ValueError("la interpretación no puede incluir resultados")
    out = consulta_vacia()
    if crudo.get("territorio"):
        out["territorio"] = str(crudo["territorio"]).strip() or None
    dane = str(crudo.get("territorio_dane") or "").strip()
    out["territorio_dane"] = dane if len(dane) == 5 and dane.isdigit() else None
    estado = crudo.get("estado_contrato")
    if estado in ESTADOS_CONTRATO or estado == "ACTIVO":
        out["estado_contrato"] = estado
    cat = crudo.get("categoria_reporte")
    if cat in CATEGORIAS_REPORTE:
        out["categoria_reporte"] = cat
    periodo = crudo.get("periodo")
    if isinstance(periodo, dict):
        desde = str(periodo.get("desde") or "").strip() or None
        hasta = str(periodo.get("hasta") or "").strip() or None
        if desde or hasta:
            out["periodo"] = {"desde": desde, "hasta": hasta}
    out["con_reportes"] = bool(crudo.get("con_reportes"))
    rel = crudo.get("con_relacion")
    if rel in {True, "SUGERIDA", "CONFIRMADA"}:
        out["con_relacion"] = rel
    texto = str(crudo.get("texto") or "").strip() or None
    out["texto"] = texto
    return out
