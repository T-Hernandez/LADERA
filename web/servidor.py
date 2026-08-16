"""Sirve la interfaz de la Fase 1 y el JSON canónico."""

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

WEB = Path(__file__).resolve().parent
CATEGORIAS = {
    "OBRA_INCONCLUSA",
    "OBRA_DETERIORADA",
    "OBRA_NO_VISIBLE",
    "PROBLEMA_PERSISTENTE",
    "RIESGO",
    "OTRO",
}

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

    for reporte in _reportes_locales():
        rid = reporte["id"]
        datos["reportes"][rid] = reporte
        dane = reporte["ubicacion"]["dane"]
        mun = datos["municipios"].get(dane)
        if mun is None:
            extra = por_dane.get(dane, {"nombre": dane, "dane": dane})
            mun = {
                "nombre": extra["nombre"],
                "dane": dane,
                "contratos": 0,
                "reportes": 0,
                "plata_total": 0,
                "contrato_ids": [],
                "reporte_ids": [],
            }
            datos["municipios"][dane] = mun
        if rid not in mun["reporte_ids"]:
            mun["reporte_ids"].append(rid)
        mun["reportes"] = len(mun["reporte_ids"])

    datos["resumen"]["contratos"] = len(datos["contratos"])
    datos["resumen"]["reportes"] = len(datos["reportes"])
    datos["resumen"]["relaciones"] = len(datos["relaciones"])
    datos["resumen"]["municipios_con_contratos"] = sum(
        1 for m in datos["municipios"].values() if m["contratos"] > 0
    )
    datos["resumen"]["municipios_con_reportes"] = sum(
        1 for m in datos["municipios"].values() if m["reportes"] > 0
    )
    return datos


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"ok": True, "fase": 1})


@app.get("/api/datos")
def api_datos():
    return jsonify(ensamblar_datos())


@app.post("/api/reportes")
def api_crear_reporte():
    cuerpo = request.get_json(silent=True) or {}
    descripcion = str(cuerpo.get("descripcion") or "").strip()
    categoria = str(cuerpo.get("categoria") or "").strip()
    dane = str(cuerpo.get("dane") or "").strip()
    fecha_obs = str(cuerpo.get("fecha_observacion") or "").strip()
    autor = str(cuerpo.get("autor") or "ciudadano (local)").strip()
    detalle = str(cuerpo.get("detalle") or "").strip()

    if not descripcion or categoria not in CATEGORIAS or not dane or not fecha_obs:
        return jsonify({"error": "Faltan campos obligatorios o la categoría no es válida."}), 400

    lookup = _leer_json(LOOKUP_MUNICIPIOS, {})
    por_dane = {item["dane"]: item for item in lookup.values()}
    if dane not in por_dane:
        return jsonify({"error": "El municipio no está en el piloto de Antioquia."}), 400

    reporte = {
        "id": f"REP-L-{uuid.uuid4().hex[:8]}",
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        "fecha_observacion": fecha_obs,
        "descripcion": descripcion,
        "categoria": categoria,
        "estado": "PUBLICADO",
        "autor": autor,
        "ubicacion": {
            "dane": dane,
            "nombre": por_dane[dane]["nombre"],
            "detalle": detalle or None,
            "lat": None,
            "lng": None,
        },
        "evidencias": [],
    }

    REPORTES_LOCALES.parent.mkdir(parents=True, exist_ok=True)
    actuales = _reportes_locales()
    actuales.append(reporte)
    REPORTES_LOCALES.write_text(
        json.dumps(actuales, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return jsonify(reporte), 201


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
