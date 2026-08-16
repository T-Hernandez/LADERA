"""Sirve la interfaz. El JSON canónico pasa por el modelo de la Fase 2."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    FIXTURE_DATOS,
    GEOJSON_MUNICIPIOS,
    HOST,
    LOOKUP_MUNICIPIOS,
    PUERTO,
    REPORTES_LOCALES,
)
from modelo import ModeloInvalido, reporte, validar_conjunto  # noqa: E402

WEB = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(WEB), static_url_path="")


def _leer_json(ruta: Path, vacio):
    if not ruta.exists():
        return vacio
    return json.loads(ruta.read_text(encoding="utf-8"))


def _reportes_locales() -> list[dict]:
    crudo = _leer_json(REPORTES_LOCALES, [])
    if isinstance(crudo, list):
        return crudo
    return []


def ensamblar_datos() -> dict:
    datos = _leer_json(FIXTURE_DATOS, None)
    if datos is None:
        raise FileNotFoundError(f"Falta el fixture: {FIXTURE_DATOS}")

    lookup = _leer_json(LOOKUP_MUNICIPIOS, {})
    por_dane = {item["dane"]: item for item in lookup.values()}
    validos = set(por_dane)

    for crudo in _reportes_locales():
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

    return validar_conjunto(datos)


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"ok": True, "fase": 2})


@app.get("/api/datos")
def api_datos():
    try:
        return jsonify(ensamblar_datos())
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/reportes")
def api_crear_reporte():
    cuerpo = request.get_json(silent=True) or {}
    lookup = _leer_json(LOOKUP_MUNICIPIOS, {})
    por_dane = {item["dane"]: item for item in lookup.values()}
    dane = str(cuerpo.get("dane") or "").strip()
    try:
        creado = reporte(
            id=f"REP-L-{uuid.uuid4().hex[:8]}",
            fecha_creacion=datetime.now(timezone.utc).isoformat(),
            fecha_observacion=str(cuerpo.get("fecha_observacion") or "").strip(),
            descripcion=str(cuerpo.get("descripcion") or "").strip(),
            categoria=str(cuerpo.get("categoria") or "").strip(),
            estado="PUBLICADO",
            autor=str(cuerpo.get("autor") or "ciudadano (local)").strip() or "ciudadano (local)",
            ubicacion={
                "dane": dane,
                "nombre": por_dane.get(dane, {}).get("nombre") or dane,
                "detalle": str(cuerpo.get("detalle") or "").strip() or None,
                "lat": None,
                "lng": None,
            },
            evidencias=[],
            municipios_validos=set(por_dane),
        )
    except ModeloInvalido as exc:
        return jsonify({"error": str(exc)}), 400

    REPORTES_LOCALES.parent.mkdir(parents=True, exist_ok=True)
    actuales = _reportes_locales()
    actuales.append(creado)
    REPORTES_LOCALES.write_text(
        json.dumps(actuales, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return jsonify(creado), 201


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
