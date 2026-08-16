"""Ejecuta filtros sobre el conjunto. No inventa filas ni URLs."""

from __future__ import annotations

from datetime import date

from mapa.capas import contrato_en_estado
from modelo.constantes import ESTADOS_REPORTE_VISIBLES
from modelo.texto import norm_busqueda


def _fecha(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _en_periodo_contrato(contrato: dict, periodo: dict | None) -> bool:
    if not periodo:
        return True
    desde = _fecha(periodo.get("desde")) or date.min
    hasta = _fecha(periodo.get("hasta")) or date.max
    ini = _fecha(contrato.get("fecha_inicio")) or _fecha(contrato.get("fecha_firma"))
    fin = _fecha(contrato.get("fecha_fin")) or ini
    if ini is None:
        return False
    return ini <= hasta and fin >= desde


def _en_periodo_reporte(reporte: dict, periodo: dict | None) -> bool:
    if not periodo:
        return True
    obs = _fecha(reporte.get("fecha_observacion"))
    if obs is None:
        return False
    desde = _fecha(periodo.get("desde")) or date.min
    hasta = _fecha(periodo.get("hasta")) or date.max
    return desde <= obs <= hasta


def _texto_contrato(c: dict) -> str:
    lugares = " ".join(
        f"{u.get('nombre') or ''} {u.get('fragmento') or ''}" for u in (c.get("ubicaciones") or [])
    )
    return " ".join(
        [c.get("id") or "", c.get("objeto") or "", c.get("entidad") or "", c.get("municipio_nombre") or "", c.get("texto_original") or "", lugares]
    )


def _texto_reporte(r: dict) -> str:
    u = r.get("ubicacion") or {}
    return " ".join(
        [r.get("id") or "", r.get("descripcion") or "", r.get("categoria") or "", u.get("nombre") or "", u.get("detalle") or "", r.get("autor") or ""]
    )


def _contiene(texto: str, needles: str) -> bool:
    cuerpo = norm_busqueda(texto)
    return all(tok in cuerpo for tok in norm_busqueda(needles).split() if tok)


def _pares_relacion(datos: dict, modo) -> set[tuple[str, str]]:
    pares = set()
    for rel in datos.get("relaciones") or []:
        if rel.get("estado") == "DESCARTADA":
            continue
        if modo == "CONFIRMADA" and rel.get("estado") != "CONFIRMADA":
            continue
        if modo == "SUGERIDA" and rel.get("estado") != "SUGERIDA":
            continue
        cid = rid = None
        for extremo in (rel["origen"], rel["destino"]):
            if extremo["tipo"] == "contrato":
                cid = extremo["id"]
            elif extremo["tipo"] == "reporte":
                rid = extremo["id"]
        if cid and rid:
            pares.add((cid, rid))
    return pares


def ejecutar(datos: dict, filtros: dict) -> dict:
    dane = filtros.get("territorio_dane")
    periodo = filtros.get("periodo")
    texto = filtros.get("texto")
    cat = filtros.get("categoria_reporte")
    estado = filtros.get("estado_contrato")

    contratos = []
    for c in datos["contratos"].values():
        if dane and c.get("municipio_dane") != dane:
            continue
        if not contrato_en_estado(c, estado):
            continue
        if not _en_periodo_contrato(c, periodo):
            continue
        if texto and not _contiene(_texto_contrato(c), texto):
            continue
        contratos.append(c)

    reportes = []
    for r in datos["reportes"].values():
        if r.get("estado") not in ESTADOS_REPORTE_VISIBLES:
            continue
        if dane and (r.get("ubicacion") or {}).get("dane") != dane:
            continue
        if cat and r.get("categoria") != cat:
            continue
        if not _en_periodo_reporte(r, periodo):
            continue
        if texto and not _contiene(_texto_reporte(r), texto):
            continue
        reportes.append(r)

    pares = _pares_relacion(datos, True)
    if filtros.get("con_relacion"):
        pares = _pares_relacion(datos, filtros["con_relacion"])
        ids_c_rel = {c for c, _ in pares}
        ids_r_rel = {r for _, r in pares}
        contratos = [c for c in contratos if c["id"] in ids_c_rel]
        reportes = [r for r in reportes if r["id"] in ids_r_rel]

    if filtros.get("con_reportes"):
        ids_r = {r["id"] for r in reportes}
        ids_c_con_rep = {c for c, rid in pares if rid in ids_r}
        contratos = [c for c in contratos if c["id"] in ids_c_con_rep]
        ids_c = {c["id"] for c in contratos}
        reportes = [r for r in reportes if r["id"] in {rid for cid, rid in pares if cid in ids_c}]

    fuentes = []
    vistos = set()
    for c in contratos:
        url = c.get("url_fuente")
        clave = ("contrato", c["id"], url)
        if clave in vistos:
            continue
        vistos.add(clave)
        fuentes.append(
            {
                "tipo": "contrato",
                "id": c["id"],
                "fuente": c.get("fuente"),
                "url_fuente": url,
            }
        )
    for r in reportes:
        fuentes.append({"tipo": "reporte", "id": r["id"], "fuente": "observacion ciudadana", "url_fuente": None})

    return {
        "contratos": contratos,
        "reportes": reportes,
        "fuentes": fuentes,
    }
