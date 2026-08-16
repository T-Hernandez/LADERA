"""Bitácora de acciones sensibles. Explica por qué un reporte tiene un estado."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import AUDITORIA_LOCAL


def leer_auditoria(ruta: Path = AUDITORIA_LOCAL) -> list[dict]:
    if not ruta.exists():
        return []
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    return crudo if isinstance(crudo, list) else []


def registrar(
    *,
    actor: str,
    accion: str,
    objeto: dict,
    resultado: str,
    motivo: str | None = None,
    fecha: datetime | None = None,
    ruta: Path = AUDITORIA_LOCAL,
) -> dict:
    evento = {
        "actor": (actor or "local").strip() or "local",
        "accion": accion,
        "fecha": (fecha or datetime.now(timezone.utc)).isoformat(),
        "objeto": objeto,
        "resultado": resultado,
        "motivo": (motivo or "").strip() or None,
    }
    actuales = leer_auditoria(ruta)
    actuales.append(evento)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(actuales, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evento


def eventos_de(objeto_id: str, ruta: Path = AUDITORIA_LOCAL) -> list[dict]:
    return [e for e in leer_auditoria(ruta) if (e.get("objeto") or {}).get("id") == objeto_id]
