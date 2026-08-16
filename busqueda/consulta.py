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


def combinar_filtros(reglas: dict, ia: dict | None) -> tuple[dict, list[str]]:
    """Reglas es la base; la IA solo agrega lo que reglas no detectó.

    Política: REGLAS > IA cuando hay conflicto explícito (mismo campo, valores
    distintos) — la IA nunca reemplaza en silencio un filtro que las reglas ya
    detectaron. Devuelve (filtros_combinados, campos_en_conflicto).
    """
    combinado = dict(reglas) if reglas else consulta_vacia()
    ia = ia or {}
    conflictos: list[str] = []

    dane_r = combinado.get("territorio_dane")
    dane_i = ia.get("territorio_dane")
    if not dane_r and dane_i:
        combinado["territorio_dane"] = dane_i
        combinado["territorio"] = ia.get("territorio")
    elif dane_r and dane_i and dane_i != dane_r:
        conflictos.append("territorio")

    for clave in ("estado_contrato", "categoria_reporte", "periodo", "texto"):
        val_r = combinado.get(clave)
        val_i = ia.get(clave)
        if not val_r and val_i:
            combinado[clave] = val_i
        elif val_r and val_i and val_i != val_r:
            conflictos.append(clave)

    for clave in ("con_reportes", "con_relacion"):
        val_r = combinado.get(clave)
        val_i = ia.get(clave)
        if not val_r and val_i:
            combinado[clave] = val_i

    return combinado, conflictos


def filtros_con_contenido(filtros: dict) -> bool:
    """True si al menos un filtro real quedó definido (no el objeto vacío)."""
    vacio = consulta_vacia()
    return any(filtros.get(clave) != vacio[clave] for clave in CLAVES)
