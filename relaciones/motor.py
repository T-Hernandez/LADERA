"""Motor de contraste por reglas. No usa IA y no confirma."""

from __future__ import annotations

import hashlib
from datetime import date

from modelo import relacion
from modelo.texto import norm_busqueda

STOP = frozenset(
    {
        "ante",
        "como",
        "con",
        "contra",
        "del",
        "desde",
        "donde",
        "este",
        "esta",
        "hacia",
        "hasta",
        "para",
        "por",
        "que",
        "sin",
        "sobre",
        "una",
        "uno",
        "los",
        "las",
        "del",
        "hay",
        "obra",
        "obras",
        "municipio",
    }
)

PALABRAS_CATEGORIA = {
    "OBRA_INCONCLUSA": ("inconclus", "incompleta", "sin terminar", "muro", "contencion"),
    "OBRA_DETERIORADA": ("deterior", "grieta", "colaps", "dano"),
    "OBRA_NO_VISIBLE": ("no visible", "sin senal", "no aparece", "no hay"),
    "PROBLEMA_PERSISTENTE": ("persist", "sigue", "reiterad"),
    "RIESGO": ("riesgo", "desliz", "masa", "carcav", "talud", "ladera", "escorrent"),
    "OTRO": (),
}


def _fecha(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _tokens(texto: str) -> set[str]:
    return {
        t
        for t in norm_busqueda(texto).split()
        if len(t) >= 4 and t not in STOP
    }


def _texto_contrato(contrato: dict) -> str:
    lugares = " ".join(
        f"{u.get('nombre') or ''} {u.get('fragmento') or ''}"
        for u in (contrato.get("ubicaciones") or [])
    )
    return " ".join(
        [
            contrato.get("objeto") or "",
            contrato.get("texto_original") or "",
            lugares,
        ]
    )


def _mismo_territorio(reporte: dict, contrato: dict) -> bool:
    return (reporte.get("ubicacion") or {}).get("dane") == contrato.get("municipio_dane")


def _lugar_especifico(reporte: dict, contrato: dict) -> bool:
    detalle = ((reporte.get("ubicacion") or {}).get("detalle") or "").strip()
    if len(norm_busqueda(detalle)) < 4:
        return False
    cuerpo = norm_busqueda(_texto_contrato(contrato))
    frag = norm_busqueda(detalle)
    if frag in cuerpo:
        return True
    return any(tok in cuerpo for tok in _tokens(detalle))


def _tiempo_compatible(reporte: dict, contrato: dict) -> bool:
    obs = _fecha(reporte.get("fecha_observacion"))
    if obs is None:
        return False
    ini = _fecha(contrato.get("fecha_inicio"))
    fin = _fecha(contrato.get("fecha_fin"))
    firma = _fecha(contrato.get("fecha_firma"))
    if ini and fin:
        return ini <= obs <= fin
    if ini and not fin:
        return obs >= ini
    if firma:
        return abs((obs - firma).days) <= 365 * 3
    return False


def _categoria_en_objeto(reporte: dict, contrato: dict) -> bool:
    cuerpo = norm_busqueda(contrato.get("objeto") or "")
    return any(p in cuerpo for p in PALABRAS_CATEGORIA.get(reporte.get("categoria") or "", ()))


def _similitud(reporte: dict, contrato: dict) -> float:
    a = _tokens(reporte.get("descripcion") or "")
    b = _tokens(_texto_contrato(contrato))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _id_par(reporte_id: str, contrato_id: str) -> str:
    crudo = f"{reporte_id}|{contrato_id}".encode("utf-8")
    return "REL-R-" + hashlib.sha256(crudo).hexdigest()[:10]


def puntuar_par(reporte: dict, contrato: dict) -> dict | None:
    """Si hay señales suficientes, devuelve un dict listo para relacion(). Si no, None."""
    if not _mismo_territorio(reporte, contrato):
        return None

    lugar = _lugar_especifico(reporte, contrato)
    tiempo = _tiempo_compatible(reporte, contrato)
    categoria = _categoria_en_objeto(reporte, contrato)
    sim = _similitud(reporte, contrato)
    semantica = categoria or sim >= 0.12

    if not (lugar or (tiempo and semantica) or sim >= 0.2):
        return None

    score = 0.4
    senales: list[str] = ["TERRITORIAL"]
    partes = [f"Mismo municipio ({contrato.get('municipio_nombre') or contrato.get('municipio_dane')})"]

    if lugar:
        score += 0.15
        detalle = (reporte.get("ubicacion") or {}).get("detalle")
        partes.append(f"el reporte sitúa el hecho en {detalle}, presente en el objeto del contrato")
    if tiempo:
        score += 0.25
        senales.append("TEMPORAL")
        partes.append(
            f"la observación ({reporte.get('fecha_observacion')}) es compatible con la vigencia del contrato"
        )
    if semantica:
        score += 0.1 if categoria else 0.0
        score += min(0.15, round(sim, 2))
        senales.append("SEMANTICA")
        partes.append("el objeto y lo observado comparten términos")

    tipos = set(senales)
    if lugar:
        tipos.add("TERRITORIAL")
    tipo = "COMPUESTA" if len(tipos) >= 2 or (lugar and (tiempo or semantica)) else next(iter(tipos))
    if lugar and not tiempo and not semantica:
        tipo = "TERRITORIAL"

    evidencia = (
        "; ".join(partes)
        + ". Esto no afirma que el contrato sea responsable ni que la obra se haya ejecutado."
    )
    return {
        "id": _id_par(reporte["id"], contrato["id"]),
        "reporte_id": reporte["id"],
        "contrato_id": contrato["id"],
        "tipo_relacion": tipo,
        "score": min(1.0, round(score, 2)),
        "evidencia": evidencia,
        "senales": senales,
    }


def _a_relacion(candidato: dict, creado_en: str, ids_contrato: set[str], ids_reporte: set[str]) -> dict:
    return relacion(
        id=candidato["id"],
        origen={"tipo": "reporte", "id": candidato["reporte_id"]},
        destino={"tipo": "contrato", "id": candidato["contrato_id"]},
        tipo_relacion=candidato["tipo_relacion"],
        metodo="REGLAS",
        estado="SUGERIDA",
        evidencia=candidato["evidencia"],
        creado_en=creado_en,
        confianza=candidato["score"],
        ids_contrato=ids_contrato,
        ids_reporte=ids_reporte,
    )


def clave_par(rel: dict) -> tuple[str, str]:
    ids = []
    for extremo in (rel["origen"], rel["destino"]):
        ids.append(extremo["id"])
    return tuple(sorted(ids))


def sugerir_relaciones(
    reportes: dict,
    contratos: dict,
    *,
    existentes: list[dict] | None = None,
    creado_en: str = "2026-08-15T00:00:00+00:00",
) -> list[dict]:
    """Sugiere pares nuevos. Nunca CONFIRMADA. No pisa un par que ya existe."""
    vistos = {clave_par(rel) for rel in (existentes or [])}
    ids_c = set(contratos)
    ids_r = set(reportes)
    salida = []
    for reporte in reportes.values():
        for contrato in contratos.values():
            par = tuple(sorted([reporte["id"], contrato["id"]]))
            if par in vistos:
                continue
            cand = puntuar_par(reporte, contrato)
            if cand is None:
                continue
            rel = _a_relacion(cand, creado_en, ids_c, ids_r)
            if rel["estado"] == "CONFIRMADA":
                continue
            salida.append(rel)
            vistos.add(par)
    return salida
