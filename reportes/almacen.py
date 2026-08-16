"""Guarda observaciones y evidencias. La foto no viaja dentro del texto."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from config import DIR_EVIDENCIAS, EVIDENCIA_MAX_BYTES, REPORTES_LOCALES
from modelo import ModeloInvalido, reporte
from reportes.territorio import municipio_en_punto

TIPOS_FOTO = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

_NOMBRE_SEGURO = re.compile(r"^EV-[a-f0-9]{8}\.(jpg|png|webp|gif)$")


class ReporteError(ValueError):
    pass


def leer_reportes(ruta: Path = REPORTES_LOCALES) -> list[dict]:
    if not ruta.exists():
        return []
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    return crudo if isinstance(crudo, list) else []


def _escribir_reportes(filas: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ruta_evidencia(reporte_id: str, nombre: str, dir_evidencias: Path = DIR_EVIDENCIAS) -> Path:
    if not _NOMBRE_SEGURO.match(nombre) or "/" in reporte_id or "\\" in reporte_id:
        raise ReporteError("ruta de evidencia no permitida")
    if not re.fullmatch(r"REP-L-[a-f0-9]{8}", reporte_id):
        raise ReporteError("id de reporte no permitido")
    return dir_evidencias / reporte_id / nombre


def _ext_foto(nombre: str, content_type: str) -> str:
    tipo = (content_type or "").split(";")[0].strip().casefold()
    if tipo in TIPOS_FOTO:
        return TIPOS_FOTO[tipo]
    sufijo = Path(nombre or "").suffix.casefold()
    if sufijo in {".jpg", ".jpeg"}:
        return ".jpg"
    if sufijo in {".png", ".webp", ".gif"}:
        return sufijo
    raise ReporteError("la evidencia tiene que ser una fotografía (jpg, png, webp o gif)")


def guardar_foto(
    reporte_id: str,
    evidencia_id: str,
    datos: bytes,
    *,
    filename: str,
    content_type: str,
    dir_evidencias: Path,
    max_bytes: int = EVIDENCIA_MAX_BYTES,
) -> tuple[str, str, str]:
    if not datos:
        raise ReporteError("la fotografía está vacía")
    if len(datos) > max_bytes:
        raise ReporteError(f"la fotografía supera {max_bytes} bytes")
    ext = _ext_foto(filename, content_type)
    nombre = f"{evidencia_id}{ext}"
    destino = dir_evidencias / reporte_id
    destino.mkdir(parents=True, exist_ok=True)
    archivo = destino / nombre
    archivo.write_bytes(datos)
    url = f"/api/evidencias/{reporte_id}/{nombre}"
    return url, nombre, content_type or TIPOS_FOTO.get(ext, "image/jpeg")


def crear_observacion(
    cuerpo: dict,
    archivo=None,
    *,
    lookup: dict,
    geojson: dict,
    ahora: datetime | None = None,
    ruta_reportes: Path = REPORTES_LOCALES,
    dir_evidencias: Path = DIR_EVIDENCIAS,
    max_bytes: int = EVIDENCIA_MAX_BYTES,
    hoy: date | None = None,
) -> dict:
    """Crea un reporte completo. No pide ni guarda un contrato."""
    ahora = ahora or datetime.now(timezone.utc)
    hoy = hoy or date.today()
    por_dane = {item["dane"]: item for item in lookup.values()}

    try:
        lat = float(cuerpo.get("lat"))
        lng = float(cuerpo.get("lng"))
    except (TypeError, ValueError) as exc:
        raise ReporteError("marca un punto en el mapa") from exc

    hallado = municipio_en_punto(
        lat,
        lng,
        geojson,
        prefer_dane=str(cuerpo.get("dane") or "").strip() or None,
    )
    if hallado is None:
        raise ReporteError("el punto no está en un municipio de Antioquia")
    dane = hallado["dane"]
    nombre = por_dane.get(dane, {}).get("nombre") or hallado["nombre"]

    fecha_obs = str(cuerpo.get("fecha_observacion") or "").strip()
    try:
        dia = date.fromisoformat(fecha_obs)
    except ValueError as exc:
        raise ReporteError("la fecha de la observación debe ser YYYY-MM-DD") from exc
    if dia > hoy:
        raise ReporteError("la fecha de la observación no puede ser futura")

    ident = f"REP-L-{uuid.uuid4().hex[:8]}"
    ev_id = f"EV-{uuid.uuid4().hex[:8]}"
    evidencias = []
    if archivo is not None:
        datos = archivo.read() if hasattr(archivo, "read") else archivo
        if datos:
            filename = getattr(archivo, "filename", "") or ""
            content_type = getattr(archivo, "content_type", "") or ""
            url, _nombre, tipo = guardar_foto(
                ident,
                ev_id,
                datos,
                filename=filename,
                content_type=content_type,
                dir_evidencias=dir_evidencias,
                max_bytes=max_bytes,
            )
            evidencias.append(
                {
                    "id": ev_id,
                    "tipo": "foto",
                    "url": url,
                    "fecha": fecha_obs,
                    "metadata": {
                        "nombre_original": Path(filename).name[:80] if filename else "",
                        "content_type": tipo,
                    },
                }
            )

    try:
        creado = reporte(
            id=ident,
            fecha_creacion=ahora.isoformat(),
            fecha_observacion=fecha_obs,
            descripcion=str(cuerpo.get("descripcion") or "").strip(),
            categoria=str(cuerpo.get("categoria") or "").strip(),
            estado="EN_REVISION",
            autor=str(cuerpo.get("autor") or "ciudadano (local)").strip() or "ciudadano (local)",
            ubicacion={
                "dane": dane,
                "nombre": nombre,
                "detalle": str(cuerpo.get("detalle") or "").strip() or None,
                "lat": lat,
                "lng": lng,
            },
            evidencias=evidencias,
            municipios_validos=set(por_dane),
        )
    except ModeloInvalido as exc:
        raise ReporteError(str(exc)) from exc

    actuales = leer_reportes(ruta_reportes)
    actuales.append(creado)
    _escribir_reportes(actuales, ruta_reportes)
    return creado
