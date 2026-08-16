"""Rutas y parámetros ajustables. El frontend no decide esto."""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

GEOJSON_MUNICIPIOS = RAIZ / "municipios_antioquia.geojson"
LOOKUP_MUNICIPIOS = RAIZ / "municipios_lookup.json"
FIXTURE_DATOS = RAIZ / "data" / "fixtures" / "datos.json"
REPORTES_LOCALES = RAIZ / "data" / "interim" / "reportes_locales.json"
DIR_RAW = RAIZ / "data" / "raw"
DIR_METADATA = RAIZ / "data" / "metadata"
MANIFIESTO = DIR_METADATA / "ingestion_manifest.json"

HOST = "127.0.0.1"
PUERTO = 5000

# SECOP II vía datos.gov.co. No se scrapea community.secop.gov.co.
SECOP_RECURSO = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
SECOP_DATASET = "jbjy-vk9h"
SECOP_FUENTE = "SECOP II — Contratos Electrónicos (Colombia Compra Eficiente / datos.gov.co)"
SECOP_WHERE = (
    "departamento='Antioquia' AND tipo_de_contrato='Obra' "
    "AND fecha_de_firma>='2019-01-01'"
)
SECOP_LIMIT = 1000
SECOP_TIMEOUT = 60
SECOP_APP_TOKEN = os.environ.get("DATOS_GOV_APP_TOKEN") or None
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_FINAL = RAIZ / "data" / "final"
CURACION_LIMPIO = DIR_INTERIM / "contratos_limpios.csv"
CURACION_REVISAR = DIR_INTERIM / "contratos_revisar.csv"
CURACION_EXCLUIDOS = DIR_INTERIM / "contratos_excluidos.csv"
CURACION_REPORTE = DIR_FINAL / "reporte_curacion.txt"
CURACION_MANIFIESTO = DIR_METADATA / "curacion_manifest.json"
RESOLUCION_SALIDA = DIR_INTERIM / "contratos_resueltos.csv"
RESOLUCION_REPORTE = DIR_FINAL / "reporte_resolucion.txt"
RESOLUCION_MANIFIESTO = DIR_METADATA / "resolucion_manifest.json"

# Variantes de ciudad que el lookup no trae con ese texto. No alias cortos ambiguos.
MUNICIPIO_ALIAS = {
    "don matias": "05237",
    "donmatias": "05237",
    "santafe de antioquia": "05042",
    "santa fe de antioquia": "05042",
    "santafedeantioquia": "05042",
    "san vicente": "05674",
    "san pedro uraba": "05665",
}

# Un nombre corto que cubre más de un municipio. No se resuelve solo.
MUNICIPIO_AMBIGUO = {
    "san pedro": ("05664", "05665"),
}

CIUDADES_VACIAS = (
    "no definido",
    "no aplica",
    "n/a",
    "na",
    "sin definir",
    "sin informacion",
    "sin información",
)

# No se reemplaza un valor raro por una estimación.
VALOR_MINIMO_USABLE = 10_000
DIAS_PROXIMO_A_VENCER = 90

SECOP_COLUMNAS = (
    "id_contrato",
    "objeto_del_contrato",
    "nombre_entidad",
    "ciudad",
    "departamento",
    "tipo_de_contrato",
    "fecha_de_firma",
    "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato",
    "estado_contrato",
    "valor_del_contrato",
    "proveedor_adjudicado",
    "urlproceso",
    "proceso_de_compra",
    "referencia_del_contrato",
)
