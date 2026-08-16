"""Mide contraste, no popularidad."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import median

from modelo.constantes import ESTADOS_REPORTE_VISIBLES
from piloto.alcance import alcance_piloto
from piloto.eventos import leer_eventos
from reportes.auditoria import leer_auditoria

PREGUNTA_CENTRAL = (
    "¿La plataforma permitió descubrir o contrastar información que antes era difícil de relacionar?"
)


def _cuando(evento: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(str(evento.get("fecha") or ""))
    except ValueError:
        return None


def _ids_extremos(rel: dict) -> tuple[str | None, str | None]:
    cid = rid = None
    for extremo in (rel.get("origen") or {}, rel.get("destino") or {}):
        if extremo.get("tipo") == "contrato":
            cid = extremo.get("id")
        elif extremo.get("tipo") == "reporte":
            rid = extremo.get("id")
    return cid, rid


def _reportes_con_relacion(datos: dict) -> set[str]:
    ids = set()
    for rel in datos.get("relaciones") or []:
        if rel.get("estado") == "DESCARTADA":
            continue
        _, rid = _ids_extremos(rel)
        if rid:
            ids.add(rid)
    return ids


def _tiempos_hasta_encontrar(eventos: list[dict]) -> list[float]:
    por_sesion: dict[str, list[dict]] = {}
    for evento in eventos:
        sesion = evento.get("sesion")
        if not sesion:
            continue
        por_sesion.setdefault(sesion, []).append(evento)
    tiempos = []
    for filas in por_sesion.values():
        orden = sorted((e for e in filas if _cuando(e)), key=_cuando)
        inicio = next((e for e in orden if e.get("accion") in {"BUSCAR", "ABRIR_ZONA"}), None)
        hallazgo = next(
            (
                e
                for e in orden
                if e.get("accion") == "CONSULTAR"
                and (e.get("objeto") or {}).get("tipo") in {"contrato", "reporte"}
            ),
            None,
        )
        if not inicio or not hallazgo:
            continue
        t0, t1 = _cuando(inicio), _cuando(hallazgo)
        if t0 is None or t1 is None or t1 < t0:
            continue
        tiempos.append((t1 - t0).total_seconds())
    return tiempos


def _contrastes_sesion(eventos: list[dict], utiles: set[str]) -> int:
    por_sesion: dict[str, set[str]] = {}
    for evento in eventos:
        if evento.get("accion") != "CONSULTAR":
            continue
        sesion = evento.get("sesion")
        tipo = (evento.get("objeto") or {}).get("tipo")
        ident = (evento.get("objeto") or {}).get("id")
        if not sesion or tipo not in {"contrato", "reporte"}:
            continue
        por_sesion.setdefault(sesion, set()).add(tipo)
        if tipo == "reporte" and ident in utiles:
            por_sesion[sesion].add("util")
    return sum(
        1
        for tipos in por_sesion.values()
        if ("contrato" in tipos and "reporte" in tipos) or "util" in tipos
    )


def resumir_piloto(
    datos: dict,
    *,
    ruta_eventos: Path | None = None,
    ruta_auditoria: Path | None = None,
) -> dict:
    from config import AUDITORIA_LOCAL, PILOTO_EVENTOS

    eventos = leer_eventos(ruta_eventos or PILOTO_EVENTOS)
    auditoria = leer_auditoria(ruta_auditoria or AUDITORIA_LOCAL)
    visibles = [
        r
        for r in (datos.get("reportes") or {}).values()
        if r.get("estado") in ESTADOS_REPORTE_VISIBLES
    ]
    utiles_ids = _reportes_con_relacion(datos)
    utiles = [r for r in visibles if r["id"] in utiles_ids]
    rels = [r for r in (datos.get("relaciones") or []) if r.get("estado") != "DESCARTADA"]
    tiempos = _tiempos_hasta_encontrar(eventos)
    contrastes = _contrastes_sesion(eventos, utiles_ids)
    if utiles or contrastes:
        lectura = (
            "Hay contraste entre observación y contratación en este piloto. "
            "Eso no declara irregularidad ni cuenta personas."
        )
    else:
        lectura = (
            "Aún no hay un contraste registrado. "
            "El piloto sigue delimitado a Antioquia y eso no significa cero inversión."
        )
    return {
        "alcance": alcance_piloto(),
        "pregunta_central": PREGUNTA_CENTRAL,
        "lectura": lectura,
        "usuarios": None,
        "metricas": {
            "reportes_creados": sum(1 for e in auditoria if e.get("accion") == "CREAR"),
            "reportes_utiles": len(utiles),
            "reportes_duplicados": sum(1 for e in eventos if e.get("accion") == "DUPLICADO"),
            "relaciones_sugeridas": sum(1 for r in rels if r.get("estado") == "SUGERIDA"),
            "relaciones_confirmadas": sum(1 for r in rels if r.get("estado") == "CONFIRMADA"),
            "contratos_consultados": len(
                {
                    (e.get("objeto") or {}).get("id")
                    for e in eventos
                    if e.get("accion") == "CONSULTAR" and (e.get("objeto") or {}).get("tipo") == "contrato"
                }
            ),
            "busquedas_realizadas": sum(1 for e in eventos if e.get("accion") == "BUSCAR"),
            "contrastes_observados": contrastes,
            "tiempo_hasta_encontrar_segundos": {
                "n": len(tiempos),
                "mediana": median(tiempos) if tiempos else None,
            },
        },
        "nota": (
            "La métrica que importa es el contraste, no el número de usuarios. "
            "Un reporte útil es el que queda al lado de un contrato sin estar descartado. "
            "Cero contrastes no es cero inversión."
        ),
    }
