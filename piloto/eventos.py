"""Eventos del piloto. No se cuenta el número de usuarios."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import PILOTO_EVENTOS

ACCIONES = frozenset({"BUSCAR", "CONSULTAR", "ABRIR_ZONA", "DUPLICADO"})


def leer_eventos(ruta: Path = PILOTO_EVENTOS) -> list[dict]:
    if not ruta.exists():
        return []
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    return crudo if isinstance(crudo, list) else []


def registrar_evento(
    *,
    accion: str,
    sesion: str | None = None,
    objeto: dict | None = None,
    resultado: str | None = None,
    fecha: datetime | None = None,
    ruta: Path = PILOTO_EVENTOS,
) -> dict:
    if accion not in ACCIONES:
        raise ValueError("acción de piloto no permitida")
    evento = {
        "accion": accion,
        "sesion": (sesion or "").strip() or None,
        "fecha": (fecha or datetime.now(timezone.utc)).isoformat(),
        "objeto": objeto or {},
        "resultado": (resultado or "").strip() or None,
    }
    actuales = leer_eventos(ruta)
    actuales.append(evento)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(actuales, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evento
