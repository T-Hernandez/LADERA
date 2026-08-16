"""Capas del mapa de trazabilidad. No demuestra causalidad."""

from __future__ import annotations

from datetime import date

from modelo.constantes import ESTADOS_REPORTE_VISIBLES


def _fecha(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _anio_de(valor) -> int | None:
    dia = _fecha(valor)
    return dia.year if dia else None


def contrato_en_anio(contrato: dict, anio: int | None) -> bool:
    if anio is None:
        return True
    ini = _fecha(contrato.get("fecha_inicio"))
    fin = _fecha(contrato.get("fecha_fin"))
    firma = _fecha(contrato.get("fecha_firma"))
    desde = date(anio, 1, 1)
    hasta = date(anio, 12, 31)
    if ini and fin:
        return ini <= hasta and fin >= desde
    if ini:
        return ini.year <= anio
    if firma:
        return firma.year == anio
    return False


def contrato_en_estado(contrato: dict, estado: str | None) -> bool:
    if not estado:
        return True
    actual = contrato.get("estado") or ""
    if estado == "ACTIVO":
        return actual in {"ACTIVO", "PROXIMO_A_VENCER"}
    return actual == estado


def reporte_en_anio(reporte: dict, anio: int | None) -> bool:
    if anio is None:
        return True
    return _anio_de(reporte.get("fecha_observacion")) == anio


def _vacio(nombre: str, dane: str) -> dict:
    return {
        "nombre": nombre,
        "dane": dane,
        "contratos": 0,
        "activos": 0,
        "finalizados": 0,
        "proximos": 0,
        "plata": 0,
        "sin_cifra": 0,
        "reportes": 0,
        "contratos_relacionados": 0,
        "relaciones_sugeridas": 0,
        "relaciones_confirmadas": 0,
        "contrato_ids": [],
        "reporte_ids": [],
    }


def _anios_disponibles(datos: dict) -> list[int]:
    anios: set[int] = set()
    for c in datos["contratos"].values():
        for campo in ("fecha_firma", "fecha_inicio", "fecha_fin"):
            y = _anio_de(c.get(campo))
            if y:
                anios.add(y)
    for r in datos["reportes"].values():
        y = _anio_de(r.get("fecha_observacion"))
        if y:
            anios.add(y)
    return sorted(anios)


def _ids_extremos(rel: dict) -> tuple[str | None, str | None]:
    cid = rid = None
    for extremo in (rel["origen"], rel["destino"]):
        if extremo["tipo"] == "contrato":
            cid = extremo["id"]
        elif extremo["tipo"] == "reporte":
            rid = extremo["id"]
    return cid, rid


def recorte_territorial(
    datos: dict,
    *,
    anio: int | None = None,
    estado: str | None = None,
) -> dict:
    """Agregados por municipio según periodo y estado. Cero no es 'sin inversión'."""
    estado = (estado or "").strip() or None
    municipios = {
        dane: _vacio(mun["nombre"], dane) for dane, mun in datos["municipios"].items()
    }

    contratos_ok = {}
    for ident, c in datos["contratos"].items():
        if contrato_en_anio(c, anio) and contrato_en_estado(c, estado):
            contratos_ok[ident] = c
            snap = municipios[c["municipio_dane"]]
            snap["contrato_ids"].append(ident)
            if c.get("valor") is None:
                snap["sin_cifra"] += 1
            else:
                snap["plata"] += c["valor"]
            if c["estado"] == "FINALIZADO":
                snap["finalizados"] += 1
            elif c["estado"] == "PROXIMO_A_VENCER":
                snap["proximos"] += 1
                snap["activos"] += 1
            elif c["estado"] == "ACTIVO":
                snap["activos"] += 1

    reportes_ok = {}
    for ident, r in datos["reportes"].items():
        if r.get("estado") not in ESTADOS_REPORTE_VISIBLES:
            continue
        if reporte_en_anio(r, anio):
            reportes_ok[ident] = r
            municipios[r["ubicacion"]["dane"]]["reporte_ids"].append(ident)

    confirmados: dict[str, set[str]] = {dane: set() for dane in municipios}
    for rel in datos.get("relaciones") or []:
        if rel.get("estado") == "DESCARTADA":
            continue
        cid, rid = _ids_extremos(rel)
        if cid not in contratos_ok or rid not in reportes_ok:
            continue
        dane = datos["reportes"][rid]["ubicacion"]["dane"]
        snap = municipios[dane]
        if rel.get("estado") == "SUGERIDA":
            snap["relaciones_sugeridas"] += 1
        elif rel.get("estado") == "CONFIRMADA":
            snap["relaciones_confirmadas"] += 1
            if datos["contratos"][cid]["municipio_dane"] == dane:
                confirmados[dane].add(cid)

    for dane, snap in municipios.items():
        snap["contratos_relacionados"] = len(confirmados[dane])
        snap["contratos"] = len(snap["contrato_ids"])
        snap["reportes"] = len(snap["reporte_ids"])

    plata_max = max((m["plata"] for m in municipios.values()), default=0)
    return {
        "filtro": {"anio": anio, "estado": estado},
        "anios": _anios_disponibles(datos),
        "plata_max": plata_max,
        "nota": (
            "Cero contratos identificados no significa cero inversión. "
            "Ver contratación y reportes en el mismo periodo no demuestra causa."
        ),
        "municipios": municipios,
    }
