"""Recorrido único: territorio → periodo → contratos → reportes → evidencia → relaciones."""

from __future__ import annotations

from mapa.capas import recorte_territorial
from modelo.constantes import ESTADOS_REPORTE_VISIBLES

PASOS = (
    {"id": 1, "clave": "problema", "titulo": "Detectar un problema"},
    {"id": 2, "clave": "zona", "titulo": "Buscar la zona"},
    {"id": 3, "clave": "contratos", "titulo": "Observar contratos"},
    {"id": 4, "clave": "periodo", "titulo": "Consultar periodos y valores"},
    {"id": 5, "clave": "reportes", "titulo": "Revisar reportes"},
    {"id": 6, "clave": "evidencia", "titulo": "Agregar evidencia"},
    {"id": 7, "clave": "relaciones", "titulo": "Actualizar relaciones"},
    {"id": 8, "clave": "continuar", "titulo": "Continuar investigando"},
)


def _ids_extremos(rel: dict) -> tuple[str | None, str | None]:
    cid = rid = None
    for extremo in (rel["origen"], rel["destino"]):
        if extremo["tipo"] == "contrato":
            cid = extremo["id"]
        elif extremo["tipo"] == "reporte":
            rid = extremo["id"]
    return cid, rid


def armar_recorrido(
    datos: dict,
    dane: str | None = None,
    *,
    anio: int | None = None,
    estado: str | None = None,
    pregunta: str | None = None,
) -> dict:
    """Arma el hilo de una zona. Cero contratos no es cero inversión."""
    recorte = recorte_territorial(datos, anio=anio, estado=estado)
    dane = (dane or "").strip() or None
    mun = (datos.get("municipios") or {}).get(dane) if dane else None
    snap = (recorte.get("municipios") or {}).get(dane) if dane else None
    contrato_ids = list((snap or {}).get("contrato_ids") or [])
    reporte_ids = list((snap or {}).get("reporte_ids") or [])
    reportes = [datos["reportes"][i] for i in reporte_ids if i in datos.get("reportes", {})]
    hay_evidencia = any((r.get("evidencias") or []) or str(r.get("id") or "").startswith("REP-L-") for r in reportes)
    hay_foto = any(r.get("evidencias") for r in reportes)

    relaciones = []
    for rel in datos.get("relaciones") or []:
        if rel.get("estado") == "DESCARTADA":
            continue
        cid, rid = _ids_extremos(rel)
        if (cid and cid in contrato_ids) or (rid and rid in reporte_ids):
            relaciones.append(rel)

    pasos = []
    listos = {
        "problema": bool((pregunta or "").strip()) or bool(dane),
        "zona": bool(mun),
        "contratos": bool(contrato_ids),
        "periodo": bool(anio or estado or contrato_ids),
        "reportes": bool(reporte_ids),
        "evidencia": hay_evidencia,
        "relaciones": bool(relaciones),
        "continuar": bool(relaciones) or (bool(contrato_ids) and bool(reporte_ids)),
    }
    for paso in PASOS:
        pasos.append({**paso, "listo": bool(listos[paso["clave"]])})

    if not dane:
        siguiente = "zona"
    elif not reporte_ids:
        siguiente = "evidencia"
    elif not relaciones:
        siguiente = "relaciones"
    else:
        siguiente = "continuar"

    return {
        "zona": {
            "dane": dane,
            "nombre": (mun or {}).get("nombre") if mun else None,
        },
        "filtro": {"anio": anio, "estado": estado},
        "pregunta": (pregunta or "").strip() or None,
        "pasos": pasos,
        "siguiente": siguiente,
        "contrato_ids": contrato_ids,
        "reporte_ids": reporte_ids,
        "relacion_ids": [r["id"] for r in relaciones],
        "resumen": {
            "contratos": len(contrato_ids),
            "reportes": len(reporte_ids),
            "relaciones": len(relaciones),
            "sugeridas": sum(1 for r in relaciones if r.get("estado") == "SUGERIDA"),
            "confirmadas": sum(1 for r in relaciones if r.get("estado") == "CONFIRMADA"),
            "plata": (snap or {}).get("plata"),
            "con_evidencia_fotografica": hay_foto,
        },
        "nota": (
            "Cero contratos identificados no significa cero inversión. "
            "Una relación sugerida no verifica el reporte ni declara irregularidad. "
            "Otra persona puede seguir contrastando desde esta misma zona."
        ),
        "visibles": sorted(ESTADOS_REPORTE_VISIBLES),
    }
