"""Decisiones humanas sobre relaciones. La IA no escribe aquí."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import RELACIONES_LOCALES
from modelo import ModeloInvalido, relacion
from relaciones.motor import clave_par


class RelacionError(ValueError):
    pass


def leer_relaciones(ruta: Path = RELACIONES_LOCALES) -> list[dict]:
    if not ruta.exists():
        return []
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    return crudo if isinstance(crudo, list) else []


def _escribir(filas: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fusionar_relaciones(
    fixture: list[dict],
    locales: list[dict],
    sugeridas: list[dict],
) -> list[dict]:
    """Local pisa fixture; fixture pisa una sugerencia del motor para el mismo par."""
    por = {}
    for rel in sugeridas:
        por[clave_par(rel)] = rel
    for rel in fixture:
        por[clave_par(rel)] = rel
    for rel in locales:
        por[clave_par(rel)] = rel
    return list(por.values())


def _ids(datos: dict) -> tuple[set[str], set[str]]:
    return set(datos["contratos"]), set(datos["reportes"])


def _extremos(reporte_id: str, contrato_id: str) -> tuple[dict, dict]:
    return {"tipo": "reporte", "id": reporte_id}, {"tipo": "contrato", "id": contrato_id}


def registrar_directa(
    reporte_id: str,
    contrato_id: str,
    datos: dict,
    *,
    ruta: Path = RELACIONES_LOCALES,
    ahora: datetime | None = None,
) -> dict:
    if reporte_id not in datos["reportes"]:
        raise RelacionError("el reporte no existe")
    if contrato_id not in datos["contratos"]:
        raise RelacionError("el contrato no existe")
    ahora = ahora or datetime.now(timezone.utc)
    ids_c, ids_r = _ids(datos)
    origen, destino = _extremos(reporte_id, contrato_id)
    try:
        creado = relacion(
            id=f"REL-D-{reporte_id[-8:]}-{contrato_id[-8:]}",
            origen=origen,
            destino=destino,
            tipo_relacion="DIRECTA",
            metodo="DIRECTA",
            estado="CONFIRMADA",
            evidencia=(
                "La persona identificó este contrato al contrastar la observación. "
                "Eso no prueba que la obra se haya ejecutado ni asigna responsabilidad."
            ),
            creado_en=ahora.isoformat(),
            revisado_en=ahora.isoformat(),
            confianza=None,
            ids_contrato=ids_c,
            ids_reporte=ids_r,
        )
    except ModeloInvalido as exc:
        raise RelacionError(str(exc)) from exc

    actuales = [r for r in leer_relaciones(ruta) if clave_par(r) != clave_par(creado)]
    actuales.append(creado)
    _escribir(actuales, ruta)
    return creado


def revisar_relacion(
    rel_id: str,
    estado: str,
    actuales: list[dict],
    datos: dict,
    *,
    ruta: Path = RELACIONES_LOCALES,
    ahora: datetime | None = None,
) -> dict:
    if estado not in {"CONFIRMADA", "DESCARTADA"}:
        raise RelacionError("solo se puede confirmar o descartar")
    hallada = next((r for r in actuales if r["id"] == rel_id), None)
    if hallada is None:
        raise RelacionError("la relación no existe")
    if hallada.get("metodo") == "IA" and estado == "CONFIRMADA":
        raise RelacionError("la IA no puede crear una relación CONFIRMADA")

    ahora = ahora or datetime.now(timezone.utc)
    metodo = hallada["metodo"]
    if estado == "CONFIRMADA" and metodo == "REGLAS":
        metodo = "MANUAL"
    if metodo == "IA":
        metodo = "MANUAL"
    ids_c, ids_r = _ids(datos)
    try:
        revisada = relacion(
            id=hallada["id"],
            origen=hallada["origen"],
            destino=hallada["destino"],
            tipo_relacion=hallada["tipo_relacion"],
            metodo=metodo,
            estado=estado,
            evidencia=hallada["evidencia"],
            creado_en=hallada["creado_en"],
            revisado_en=ahora.isoformat(),
            confianza=hallada.get("confianza"),
            ids_contrato=ids_c,
            ids_reporte=ids_r,
        )
    except ModeloInvalido as exc:
        raise RelacionError(str(exc)) from exc

    locales = [r for r in leer_relaciones(ruta) if r["id"] != rel_id]
    locales.append(revisada)
    _escribir(locales, ruta)
    return revisada
