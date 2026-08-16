"""Estados de un reporte, revisión humana y la frase que los explica."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import (
    DECISIONES_REPORTES,
    SENALAMIENTOS_PARA_REVISION,
)
from modelo.constantes import ESTADOS_REPORTE, ESTADOS_REPORTE_VISIBLES
from modelo.texto import norm_busqueda
from reportes.auditoria import eventos_de, leer_auditoria, registrar

TRANSICIONES = {
    "BORRADOR": {"EN_REVISION", "RETIRADO"},
    "EN_REVISION": {"PUBLICADO", "RELACIONADO", "VERIFICADO", "DESCARTADO", "RETIRADO"},
    "PUBLICADO": {"EN_REVISION", "RELACIONADO", "VERIFICADO", "DESCARTADO", "RETIRADO"},
    "RELACIONADO": {"EN_REVISION", "PUBLICADO", "VERIFICADO", "DESCARTADO", "RETIRADO"},
    "VERIFICADO": {"EN_REVISION", "RELACIONADO", "DESCARTADO", "RETIRADO"},
    "DESCARTADO": {"EN_REVISION"},
    "RETIRADO": {"EN_REVISION"},
}

FRASES = {
    "BORRADOR": "Aún no se ha enviado. No aparece en el mapa.",
    "EN_REVISION": "Quedó en revisión. Es una observación, no un hecho verificado.",
    "PUBLICADO": "Está a la vista como observación ciudadana. Eso no lo vuelve verdadero.",
    "RELACIONADO": "Hay un vínculo con contratación. El vínculo no verifica el reporte ni declara irregularidad.",
    "VERIFICADO": "Una persona revisó esta observación. No declara que el problema sea cierto ni que haya irregularidad.",
    "DESCARTADO": "Se apartó de la superficie pública. No se borra el registro.",
    "RETIRADO": "Se retiró. Ya no aparece como observación pública.",
}


def reporte_visible(reporte: dict) -> bool:
    return (reporte or {}).get("estado") in ESTADOS_REPORTE_VISIBLES


def leer_decisiones(ruta: Path = DECISIONES_REPORTES) -> list[dict]:
    if not ruta.exists():
        return []
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    return crudo if isinstance(crudo, list) else []


def _escribir_decisiones(filas: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def estado_efectivo(reporte_id: str, estado_base: str, decisiones: list[dict]) -> str:
    ultimo = None
    for fila in decisiones:
        if fila.get("id") == reporte_id:
            ultimo = fila
    return (ultimo or {}).get("estado") or estado_base


def aplicar_decisiones(reportes: dict, decisiones: list[dict]) -> dict:
    for ident, fila in reportes.items():
        nuevo = estado_efectivo(ident, fila["estado"], decisiones)
        if nuevo != fila["estado"]:
            fila["estado"] = nuevo
    return reportes


def _es_ia(actor: str) -> bool:
    return norm_busqueda(actor) in {"ia", "modelo", "llm", "asistente"}


def _ultima_decision(eventos: list[dict]) -> dict | None:
    for evento in reversed(eventos):
        if evento.get("accion") in {"REVISAR", "RETIRAR", "CREAR", "SENALAR"}:
            return evento
    return None


def enriquecer_confianza(datos: dict, ruta_auditoria: Path) -> dict:
    por_id: dict[str, list[dict]] = {}
    for evento in leer_auditoria(ruta_auditoria):
        oid = (evento.get("objeto") or {}).get("id")
        if oid:
            por_id.setdefault(oid, []).append(evento)
    for r in datos["reportes"].values():
        evs = por_id.get(r["id"], [])
        n = sum(1 for e in evs if e.get("accion") == "SENALAR")
        r["confianza"] = explicar_estado(r, eventos=evs, senalamientos=n)
    return datos


def explicar_estado(
    reporte: dict,
    *,
    eventos: list[dict] | None = None,
    senalamientos: int = 0,
    ruta_auditoria: Path | None = None,
) -> dict:
    eventos = eventos if eventos is not None else eventos_de(reporte["id"], ruta_auditoria) if ruta_auditoria else []
    ultima = _ultima_decision(eventos)
    estado = reporte.get("estado") or ""
    partes = [FRASES.get(estado, f"Estado actual: {estado}.")]
    if ultima and ultima.get("motivo"):
        partes.append(f"Motivo registrado: {ultima['motivo']}")
    if ultima:
        partes.append(
            f"Última acción: {ultima['accion']} por {ultima['actor']} el {str(ultima['fecha'])[:10]} → {ultima['resultado']}."
        )
    elif str(reporte.get("id") or "").startswith("REP-") and not str(reporte.get("id") or "").startswith("REP-L-"):
        partes.append("El estado inicial viene del fixture de demostración, no de una verificación de campo.")
    if senalamientos:
        partes.append(f"Señalamientos de contenido: {senalamientos}.")
    return {
        "estado": estado,
        "explicacion": " ".join(partes),
        "ultima": ultima,
        "senalamientos": senalamientos,
        "decisiones": eventos,
    }


def exceso_frecuencia(
    actor: str,
    *,
    ruta_auditoria: Path,
    maximo: int,
    ahora: datetime,
    ventana_minutos: int = 60,
) -> bool:
    desde = ahora - timedelta(minutes=ventana_minutos)
    n = 0
    for evento in leer_auditoria(ruta_auditoria):
        if evento.get("accion") != "CREAR":
            continue
        if (evento.get("actor") or "") != actor:
            continue
        try:
            cuando = datetime.fromisoformat(str(evento.get("fecha") or ""))
        except ValueError:
            continue
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        if cuando >= desde:
            n += 1
    return n >= maximo


def es_duplicado(
    descripcion: str,
    dane: str,
    reportes: list[dict],
    *,
    ahora: datetime,
    horas: int,
) -> bool:
    clave = norm_busqueda(descripcion)
    if not clave:
        return False
    desde = ahora - timedelta(hours=horas)
    for r in reportes:
        if (r.get("ubicacion") or {}).get("dane") != dane:
            continue
        if r.get("estado") in {"DESCARTADO", "RETIRADO"}:
            continue
        if norm_busqueda(r.get("descripcion") or "") != clave:
            continue
        try:
            cuando = datetime.fromisoformat(str(r.get("fecha_creacion") or ""))
        except ValueError:
            return True
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        if cuando >= desde:
            return True
    return False


def _guardar_decision(
    reporte_id: str,
    estado: str,
    *,
    actor: str,
    motivo: str,
    fecha: datetime,
    ruta_decisiones: Path,
) -> dict:
    fila = {
        "id": reporte_id,
        "estado": estado,
        "actor": actor,
        "motivo": motivo,
        "fecha": fecha.isoformat(),
    }
    actuales = [d for d in leer_decisiones(ruta_decisiones) if d.get("id") != reporte_id]
    actuales.append(fila)
    _escribir_decisiones(actuales, ruta_decisiones)
    return fila


def _actualizar_local(reporte_id: str, estado: str, ruta_reportes: Path) -> None:
    from reportes.almacen import leer_reportes, escribir_reportes

    filas = leer_reportes(ruta_reportes)
    cambio = False
    for fila in filas:
        if fila.get("id") == reporte_id:
            fila["estado"] = estado
            cambio = True
    if cambio:
        escribir_reportes(filas, ruta_reportes)


def revisar_reporte(
    reporte_id: str,
    nuevo_estado: str,
    motivo: str,
    *,
    actor: str,
    reportes: dict,
    ahora: datetime | None = None,
    ruta_decisiones: Path = DECISIONES_REPORTES,
    ruta_auditoria: Path | None = None,
    ruta_reportes=None,
) -> dict:
    from config import AUDITORIA_LOCAL, REPORTES_LOCALES
    from reportes.almacen import ReporteError

    ahora = ahora or datetime.now(timezone.utc)
    ruta_auditoria = ruta_auditoria or AUDITORIA_LOCAL
    ruta_reportes = ruta_reportes or REPORTES_LOCALES
    actual = reportes.get(reporte_id)
    if actual is None:
        raise ReporteError("reporte no encontrado")
    if nuevo_estado not in ESTADOS_REPORTE:
        raise ReporteError("estado de reporte no permitido")
    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ReporteError("explica el motivo de la decisión (mínimo 10 caracteres)")
    actor = (actor or "moderación local").strip() or "moderación local"
    if nuevo_estado == "VERIFICADO" and _es_ia(actor):
        raise ReporteError("la IA no puede verificar un reporte")
    permitidos = TRANSICIONES.get(actual["estado"], set())
    if nuevo_estado != actual["estado"] and nuevo_estado not in permitidos:
        raise ReporteError(f"no se puede pasar de {actual['estado']} a {nuevo_estado}")
    _guardar_decision(
        reporte_id,
        nuevo_estado,
        actor=actor,
        motivo=motivo,
        fecha=ahora,
        ruta_decisiones=ruta_decisiones,
    )
    _actualizar_local(reporte_id, nuevo_estado, ruta_reportes)
    registrar(
        actor=actor,
        accion="REVISAR",
        objeto={"tipo": "reporte", "id": reporte_id},
        resultado=nuevo_estado,
        motivo=motivo,
        fecha=ahora,
        ruta=ruta_auditoria,
    )
    actual["estado"] = nuevo_estado
    return actual


def senalar_reporte(
    reporte_id: str,
    motivo: str,
    *,
    actor: str,
    reportes: dict,
    ahora: datetime | None = None,
    ruta_decisiones: Path = DECISIONES_REPORTES,
    ruta_auditoria: Path | None = None,
    ruta_reportes=None,
    umbral: int = SENALAMIENTOS_PARA_REVISION,
) -> dict:
    from config import AUDITORIA_LOCAL, REPORTES_LOCALES
    from reportes.almacen import ReporteError

    ahora = ahora or datetime.now(timezone.utc)
    ruta_auditoria = ruta_auditoria or AUDITORIA_LOCAL
    ruta_reportes = ruta_reportes or REPORTES_LOCALES
    actual = reportes.get(reporte_id)
    if actual is None:
        raise ReporteError("reporte no encontrado")
    if actual["estado"] in {"DESCARTADO", "RETIRADO", "BORRADOR"}:
        raise ReporteError("este reporte ya no está en la superficie pública")
    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ReporteError("explica por qué señalas este contenido (mínimo 10 caracteres)")
    actor = (actor or "ciudadano").strip() or "ciudadano"
    registrar(
        actor=actor,
        accion="SENALAR",
        objeto={"tipo": "reporte", "id": reporte_id},
        resultado=actual["estado"],
        motivo=motivo,
        fecha=ahora,
        ruta=ruta_auditoria,
    )
    senalamientos = sum(
        1
        for e in eventos_de(reporte_id, ruta_auditoria)
        if e.get("accion") == "SENALAR"
    )
    if senalamientos >= umbral and actual["estado"] in {"PUBLICADO", "RELACIONADO", "VERIFICADO"}:
        return revisar_reporte(
            reporte_id,
            "EN_REVISION",
            "varios señalamientos; vuelve a revisión",
            actor="sistema",
            reportes=reportes,
            ahora=ahora,
            ruta_decisiones=ruta_decisiones,
            ruta_auditoria=ruta_auditoria,
            ruta_reportes=ruta_reportes,
        )
    return actual


def retirar_reporte(
    reporte_id: str,
    motivo: str,
    *,
    actor: str,
    reportes: dict,
    ahora: datetime | None = None,
    ruta_decisiones: Path = DECISIONES_REPORTES,
    ruta_auditoria: Path | None = None,
    ruta_reportes=None,
) -> dict:
    return revisar_reporte(
        reporte_id,
        "RETIRADO",
        motivo or "la observación se retira de la superficie pública",
        actor=actor or "ciudadano",
        reportes=reportes,
        ahora=ahora,
        ruta_decisiones=ruta_decisiones,
        ruta_auditoria=ruta_auditoria,
        ruta_reportes=ruta_reportes,
    )
