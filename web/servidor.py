"""Sirve la interfaz. El JSON canónico pasa por el modelo de la Fase 2."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    AUDITORIA_LOCAL,
    DATOS_FINAL,
    DECISIONES_REPORTES,
    DIR_EVIDENCIAS,
    FIXTURE_DATOS,
    GEOJSON_MUNICIPIOS,
    HOST,
    LOOKUP_MUNICIPIOS,
    MODERACION_TOKEN,
    PILOTO_EVENTOS,
    PUERTO,
    RELACIONES_LOCALES,
    REPORTES_LOCALES,
)
from busqueda import buscar  # noqa: E402
from escala.activar import EscalaError, estado_escala, intentar_activar  # noqa: E402
from piloto.eventos import registrar_evento  # noqa: E402
from piloto.metricas import resumir_piloto  # noqa: E402
from producto.recorrido import armar_recorrido  # noqa: E402
from mapa.capas import recorte_territorial  # noqa: E402
from modelo import ModeloInvalido, reporte, validar_conjunto  # noqa: E402
from relaciones.almacen import (  # noqa: E402
    RelacionError,
    fusionar_relaciones,
    leer_relaciones,
    registrar_directa,
    revisar_relacion,
)
from relaciones.motor import sugerir_relaciones  # noqa: E402
from reportes.almacen import (  # noqa: E402
    ReporteError,
    crear_observacion,
    leer_reportes,
    ruta_evidencia,
)
from reportes.confianza import (  # noqa: E402
    aplicar_decisiones,
    enriquecer_confianza,
    explicar_estado,
    leer_decisiones,
    retirar_reporte,
    revisar_reporte,
    senalar_reporte,
)
from reportes.territorio import municipio_en_punto  # noqa: E402

WEB = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(WEB), static_url_path="")

_geojson = None
_lookup = None


def _leer_json(ruta: Path, vacio):
    if not ruta.exists():
        return vacio
    return json.loads(ruta.read_text(encoding="utf-8"))


def _lookup_municipios() -> dict:
    global _lookup
    if _lookup is None:
        _lookup = _leer_json(LOOKUP_MUNICIPIOS, {})
    return _lookup


def _geojson_municipios() -> dict:
    global _geojson
    if _geojson is None:
        _geojson = json.loads(GEOJSON_MUNICIPIOS.read_text(encoding="utf-8"))
    return _geojson


def _fuente_datos() -> Path:
    """Fase 3-5 real si ya corrió; el fixture solo si todavía no hay datos reales."""
    return DATOS_FINAL if DATOS_FINAL.exists() else FIXTURE_DATOS


def ensamblar_datos() -> dict:
    ruta = _fuente_datos()
    datos = _leer_json(ruta, None)
    if datos is None:
        raise FileNotFoundError(f"Falta el fixture: {FIXTURE_DATOS}")

    lookup = _lookup_municipios()
    por_dane = {item["dane"]: item for item in lookup.values()}
    validos = set(por_dane)

    for crudo in leer_reportes(REPORTES_LOCALES):
        datos["reportes"][crudo["id"]] = reporte(
            id=crudo["id"],
            fecha_creacion=crudo["fecha_creacion"],
            fecha_observacion=crudo["fecha_observacion"],
            descripcion=crudo["descripcion"],
            categoria=crudo["categoria"],
            estado=crudo["estado"],
            autor=crudo["autor"],
            ubicacion=crudo["ubicacion"],
            evidencias=crudo.get("evidencias"),
            municipios_validos=validos,
        )
    aplicar_decisiones(datos["reportes"], leer_decisiones(DECISIONES_REPORTES))

    fixture_rels = list(datos.get("relaciones") or [])
    locales = leer_relaciones(RELACIONES_LOCALES)
    sugeridas = sugerir_relaciones(
        datos["reportes"],
        datos["contratos"],
        existentes=fixture_rels + locales,
    )
    datos["relaciones"] = fusionar_relaciones(fixture_rels, locales, sugeridas)
    return enriquecer_confianza(validar_conjunto(datos), AUDITORIA_LOCAL)


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"ok": True, "fase": 13, "territorio": "Antioquia", "escala": "piloto"})


@app.get("/api/datos")
def api_datos():
    try:
        return jsonify(ensamblar_datos())
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/mapa")
def api_mapa():
    try:
        anio_crudo = (request.args.get("anio") or "").strip()
        anio = int(anio_crudo) if anio_crudo else None
        estado = (request.args.get("estado") or "").strip() or None
        datos = ensamblar_datos()
        return jsonify(recorte_territorial(datos, anio=anio, estado=estado))
    except (TypeError, ValueError):
        return jsonify({"error": "anio debe ser un número"}), 400
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/recorrido")
def api_recorrido():
    dane = str(request.args.get("dane") or "").strip() or None
    pregunta = str(request.args.get("pregunta") or "").strip() or None
    anio_crudo = (request.args.get("anio") or "").strip()
    estado = (request.args.get("estado") or "").strip() or None
    try:
        anio = int(anio_crudo) if anio_crudo else None
        datos = ensamblar_datos()
        return jsonify(
            armar_recorrido(datos, dane, anio=anio, estado=estado, pregunta=pregunta)
        )
    except (TypeError, ValueError):
        return jsonify({"error": "anio debe ser un número"}), 400
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/escala")
def api_escala():
    try:
        datos = ensamblar_datos()
        return jsonify(
            estado_escala(datos, ruta_eventos=PILOTO_EVENTOS, ruta_auditoria=AUDITORIA_LOCAL)
        )
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/escala/activar")
def api_escala_activar():
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        return jsonify(
            intentar_activar(
                str(cuerpo.get("eje") or ""),
                str(cuerpo.get("destino") or ""),
                datos,
                ruta_eventos=PILOTO_EVENTOS,
                ruta_auditoria=AUDITORIA_LOCAL,
            )
        )
    except EscalaError as exc:
        return jsonify({"error": str(exc), "mapa_activo": "municipios_antioquia.geojson"}), 409
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/piloto")
def api_piloto():
    try:
        datos = ensamblar_datos()
        return jsonify(
            resumir_piloto(datos, ruta_eventos=PILOTO_EVENTOS, ruta_auditoria=AUDITORIA_LOCAL)
        )
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/piloto/evento")
def api_piloto_evento():
    cuerpo = request.get_json(silent=True) or {}
    try:
        evento = registrar_evento(
            accion=str(cuerpo.get("accion") or "").strip(),
            sesion=str(cuerpo.get("sesion") or "").strip() or None,
            objeto=cuerpo.get("objeto") if isinstance(cuerpo.get("objeto"), dict) else {},
            resultado=str(cuerpo.get("resultado") or "").strip() or None,
            ruta=PILOTO_EVENTOS,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(evento), 201


@app.post("/api/buscar")
def api_buscar():
    cuerpo = request.get_json(silent=True) or {}
    pregunta = str(cuerpo.get("pregunta") or "").strip()
    if not pregunta:
        return jsonify({"error": "escribe una pregunta"}), 400
    dane = str(cuerpo.get("dane") or "").strip() or None
    usar_ia = bool(cuerpo.get("usar_ia"))
    try:
        datos = ensamblar_datos()
        resultado = buscar(
            pregunta,
            datos,
            _lookup_municipios(),
            dane_zona=dane,
            usar_ia=usar_ia,
        )
        registrar_evento(
            accion="BUSCAR",
            sesion=str(cuerpo.get("sesion") or "").strip() or None,
            objeto={"pregunta": pregunta, "dane": dane},
            resultado=f"{len(resultado.get('contratos') or [])} contratos, {len(resultado.get('reportes') or [])} reportes",
            ruta=PILOTO_EVENTOS,
        )
        return jsonify(resultado)
    except (ModeloInvalido, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/territorio")
def api_territorio():
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat y lng tienen que ser números"}), 400
    prefer = str(request.args.get("dane") or "").strip() or None
    hallado = municipio_en_punto(lat, lng, _geojson_municipios(), prefer_dane=prefer)
    if hallado is None:
        return jsonify({"error": "el punto no está en un municipio de Antioquia"}), 404
    lookup = _lookup_municipios()
    por_dane = {item["dane"]: item for item in lookup.values()}
    nombre = por_dane.get(hallado["dane"], {}).get("nombre") or hallado["nombre"]
    return jsonify({"dane": hallado["dane"], "nombre": nombre})


@app.post("/api/reportes")
def api_crear_reporte():
    if request.files or (request.content_type or "").startswith("multipart/"):
        cuerpo = request.form.to_dict()
        archivo = request.files.get("foto")
    else:
        cuerpo = request.get_json(silent=True) or {}
        archivo = None
    try:
        fixture = _leer_json(FIXTURE_DATOS, {}) or {}
        creado = crear_observacion(
            cuerpo,
            archivo,
            lookup=_lookup_municipios(),
            geojson=_geojson_municipios(),
            ruta_reportes=REPORTES_LOCALES,
            dir_evidencias=DIR_EVIDENCIAS,
            actor=request.remote_addr or "local",
            ruta_auditoria=AUDITORIA_LOCAL,
            otros_reportes=list((fixture.get("reportes") or {}).values()),
        )
    except ReporteError as exc:
        if "parecida" in str(exc):
            registrar_evento(
                accion="DUPLICADO",
                objeto={"dane": cuerpo.get("dane")},
                resultado=str(exc),
                ruta=PILOTO_EVENTOS,
            )
        return jsonify({"error": str(exc)}), 400
    return jsonify(creado), 201


def _actor_pedido(cuerpo: dict) -> str:
    return str(cuerpo.get("actor") or request.remote_addr or "moderación local").strip()


def _moderacion_autorizada() -> bool:
    """Candado de piloto: revisar/retirar reportes y revisar relaciones lo exigen. Señalar no."""
    if not MODERACION_TOKEN:
        return False
    recibido = request.headers.get("X-Moderacion-Token") or ""
    return recibido == MODERACION_TOKEN


def _respuesta_no_autorizada():
    return jsonify({"error": "se requiere el token de moderación"}), 401


@app.get("/api/reportes/<reporte_id>/confianza")
def api_confianza(reporte_id: str):
    try:
        datos = ensamblar_datos()
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500
    hallado = datos["reportes"].get(reporte_id)
    if hallado is None:
        return jsonify({"error": "reporte no encontrado"}), 404
    return jsonify(hallado.get("confianza") or explicar_estado(hallado, eventos=[]))


@app.post("/api/reportes/<reporte_id>/revisar")
def api_revisar_reporte(reporte_id: str):
    if not _moderacion_autorizada():
        return _respuesta_no_autorizada()
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        revisado = revisar_reporte(
            reporte_id,
            str(cuerpo.get("estado") or "").strip(),
            str(cuerpo.get("motivo") or ""),
            actor=_actor_pedido(cuerpo),
            reportes=datos["reportes"],
            ruta_decisiones=DECISIONES_REPORTES,
            ruta_auditoria=AUDITORIA_LOCAL,
            ruta_reportes=REPORTES_LOCALES,
        )
    except ReporteError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(revisado)


@app.post("/api/reportes/<reporte_id>/senalar")
def api_senalar_reporte(reporte_id: str):
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        actual = senalar_reporte(
            reporte_id,
            str(cuerpo.get("motivo") or ""),
            actor=_actor_pedido(cuerpo) if cuerpo.get("actor") else (request.remote_addr or "ciudadano"),
            reportes=datos["reportes"],
            ruta_decisiones=DECISIONES_REPORTES,
            ruta_auditoria=AUDITORIA_LOCAL,
            ruta_reportes=REPORTES_LOCALES,
        )
    except ReporteError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(actual)


@app.post("/api/reportes/<reporte_id>/retirar")
def api_retirar_reporte(reporte_id: str):
    if not _moderacion_autorizada():
        return _respuesta_no_autorizada()
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        actual = retirar_reporte(
            reporte_id,
            str(cuerpo.get("motivo") or "la observación se retira de la superficie pública"),
            actor=_actor_pedido(cuerpo) if cuerpo.get("actor") else (request.remote_addr or "ciudadano"),
            reportes=datos["reportes"],
            ruta_decisiones=DECISIONES_REPORTES,
            ruta_auditoria=AUDITORIA_LOCAL,
            ruta_reportes=REPORTES_LOCALES,
        )
    except ReporteError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(actual)


@app.post("/api/relaciones")
def api_relacion_directa():
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        creado = registrar_directa(
            str(cuerpo.get("reporte_id") or "").strip(),
            str(cuerpo.get("contrato_id") or "").strip(),
            datos,
            ruta=RELACIONES_LOCALES,
        )
    except (RelacionError, ModeloInvalido, FileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(creado), 201


@app.post("/api/relaciones/<rel_id>/revisar")
def api_revisar_relacion(rel_id: str):
    if not _moderacion_autorizada():
        return _respuesta_no_autorizada()
    cuerpo = request.get_json(silent=True) or {}
    try:
        datos = ensamblar_datos()
        revisada = revisar_relacion(
            rel_id,
            str(cuerpo.get("estado") or "").strip(),
            datos["relaciones"],
            datos,
            ruta=RELACIONES_LOCALES,
        )
    except RelacionError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(revisada)


@app.get("/api/evidencias/<reporte_id>/<nombre>")
def api_evidencia(reporte_id: str, nombre: str):
    try:
        ruta = ruta_evidencia(reporte_id, nombre, DIR_EVIDENCIAS)
    except ReporteError:
        return jsonify({"error": "evidencia no encontrada"}), 404
    if not ruta.exists():
        return jsonify({"error": "evidencia no encontrada"}), 404
    return send_from_directory(ruta.parent, ruta.name)


@app.get("/assets/municipios_antioquia.geojson")
def geojson():
    return send_from_directory(RAIZ, GEOJSON_MUNICIPIOS.name)


@app.get("/assets/municipios_lookup.json")
def lookup():
    return send_from_directory(RAIZ, LOOKUP_MUNICIPIOS.name)


def main() -> None:
    if not FIXTURE_DATOS.exists() and not DATOS_FINAL.exists():
        raise SystemExit(
            "No existe data/fixtures/datos.json ni data/final/datos.json. "
            "Ejecuta: python data/fixtures/construir_fixture.py"
        )
    app.run(host=HOST, port=PUERTO, debug=False)


if __name__ == "__main__":
    main()
