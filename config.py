"""Rutas y parámetros ajustables. El frontend no decide esto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent

GEOJSON_MUNICIPIOS = RAIZ / "municipios_antioquia.geojson"
LOOKUP_MUNICIPIOS = RAIZ / "municipios_lookup.json"
FIXTURE_DATOS = RAIZ / "data" / "fixtures" / "datos.json"
REPORTES_LOCALES = RAIZ / "data" / "interim" / "reportes_locales.json"

HOST = "127.0.0.1"
PUERTO = 5000
