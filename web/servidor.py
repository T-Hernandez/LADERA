"""Sirve la interfaz. El JSON canónico pasa por el modelo de la Fase 2."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    DIR_EVIDENCIAS,
    FIXTURE_DATOS,
    GEOJSON_MUNICIPIOS,
    HOST,
    LOOKUP_MUNICIPIOS,
    PUERTO,
    RELACIONES_LOCALES,
    REPORTES_LOCALES,
)
from busqueda import buscar  # noqa: E402
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


def ensamblar_datos() -> dict:
    datos = _leer_json(FIXTURE_DATOS, None)
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

    fixture_rels = list(datos.get("relaciones") or [])
    locales = leer_relaciones(RELACIONES_LOCALES)
    sugeridas = sugerir_relaciones(
        datos["reportes"],
        datos["contratos"],
        existentes=fixture_rels + locales,
    )
    datos["relaciones"] = fusionar_relaciones(fixture_rels, locales, sugeridas)
    return validar_conjunto(datos)


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"ok": True, "fase": 9})


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
        creado = crear_observacion(
            cuerpo,
            archivo,
            lookup=_lookup_municipios(),
            geojson=_geojson_municipios(),
            ruta_reportes=REPORTES_LOCALES,
            dir_evidencias=DIR_EVIDENCIAS,
        )
    except ReporteError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(creado), 201


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
    if not FIXTURE_DATOS.exists():
        raise SystemExit(
            "No existe data/fixtures/datos.json. "
            "Ejecuta: python data/fixtures/construir_fixture.py"
        )
    app.run(host=HOST, port=PUERTO, debug=False)


if __name__ == "__main__":
    main()
