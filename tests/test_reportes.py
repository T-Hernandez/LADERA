import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import GEOJSON_MUNICIPIOS, LOOKUP_MUNICIPIOS
from reportes.almacen import ReporteError, crear_observacion, ruta_evidencia
from reportes.territorio import municipio_en_punto

CUADRO = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"MPIO_CCNCT": "05001", "MPIO_CNMBR": "MEDELLÍN"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-76, 6], [-75, 6], [-75, 7], [-76, 7], [-76, 6]]],
            },
        }
    ],
}


def _lookup():
    return json.loads(LOOKUP_MUNICIPIOS.read_text(encoding="utf-8"))


def _geojson():
    return json.loads(GEOJSON_MUNICIPIOS.read_text(encoding="utf-8"))


class Archivo:
    def __init__(self, datos, filename="ladera.png", content_type="image/png"):
        self._datos = datos
        self.filename = filename
        self.content_type = content_type

    def read(self):
        return self._datos


class TestTerritorio(unittest.TestCase):
    def test_punto_dentro_del_cuadro(self):
        hallado = municipio_en_punto(6.5, -75.5, CUADRO)
        self.assertEqual(hallado["dane"], "05001")

    def test_punto_fuera_del_cuadro(self):
        self.assertIsNone(municipio_en_punto(0, 0, CUADRO))

    def test_medellin_del_fixture(self):
        hallado = municipio_en_punto(6.25, -75.58, _geojson())
        self.assertIsNotNone(hallado)
        self.assertEqual(hallado["dane"], "05001")

    def test_fuera_de_antioquia(self):
        self.assertIsNone(municipio_en_punto(4.61, -74.08, _geojson()))


class TestCrear(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.ruta = self.dir / "reportes.json"
        self.fotos = self.dir / "evidencias"

    def _crear(self, extra=None, archivo=None, hoy=None):
        cuerpo = {
            "descripcion": "El muro sigue a medias y hay escorrentia",
            "categoria": "OBRA_INCONCLUSA",
            "fecha_observacion": "2026-06-15",
            "lat": 6.25,
            "lng": -75.58,
            "detalle": "barrio El Popular",
            "autor": "vecina",
        }
        if extra:
            cuerpo.update(extra)
        return crear_observacion(
            cuerpo,
            archivo,
            lookup=_lookup(),
            geojson=_geojson(),
            ahora=datetime(2026, 8, 15, 21, 0, tzinfo=timezone.utc),
            ruta_reportes=self.ruta,
            dir_evidencias=self.fotos,
            hoy=hoy or date(2026, 8, 15),
        )

    def test_completo_sin_contrato(self):
        creado = self._crear()
        self.assertTrue(creado["id"].startswith("REP-L-"))
        self.assertEqual(creado["estado"], "EN_REVISION")
        self.assertEqual(creado["fecha_observacion"], "2026-06-15")
        self.assertTrue(creado["fecha_creacion"].startswith("2026-08-15"))
        self.assertEqual(creado["ubicacion"]["dane"], "05001")
        self.assertEqual(creado["ubicacion"]["lat"], 6.25)
        self.assertNotIn("contrato_id", creado)
        self.assertEqual(creado["evidencias"], [])

    def test_ignora_contrato_id(self):
        creado = self._crear({"contrato_id": "FIX-X", "id_contrato": "FIX-X"})
        self.assertNotIn("contrato_id", creado)
        self.assertNotEqual(creado.get("id"), "FIX-X")

    def test_foto_aparte_del_texto(self):
        creado = self._crear(archivo=Archivo(b"\x89PNG\r\n\x1a\nfoto"))
        self.assertEqual(len(creado["evidencias"]), 1)
        ev = creado["evidencias"][0]
        self.assertEqual(ev["tipo"], "foto")
        self.assertNotIn("foto", creado["descripcion"].casefold())
        self.assertTrue(ev["url"].startswith("/api/evidencias/"))
        nombre = ev["url"].rsplit("/", 1)[-1]
        ruta = ruta_evidencia(creado["id"], nombre, self.fotos)
        self.assertTrue(ruta.exists())
        self.assertEqual(ruta.read_bytes()[:4], b"\x89PNG")
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertNotIn("\\x89PNG", texto)

    def test_sin_punto_falla(self):
        with self.assertRaises(ReporteError):
            self._crear({"lat": "", "lng": ""})

    def test_punto_ajeno_falla(self):
        with self.assertRaises(ReporteError):
            self._crear({"lat": 4.61, "lng": -74.08})

    def test_fecha_futura_falla(self):
        with self.assertRaises(ReporteError):
            self._crear({"fecha_observacion": "2026-12-01"})

    def test_no_imagen_falla(self):
        with self.assertRaises(ReporteError):
            self._crear(archivo=Archivo(b"%PDF-1.4", "doc.pdf", "application/pdf"))

    def test_ruta_evidencia_no_sale_del_directorio(self):
        with self.assertRaises(ReporteError):
            ruta_evidencia("REP-L-abcd1234", "../secret.jpg", self.fotos)


class TestApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        from web.servidor import app

        self.client = app.test_client()
        self.patches = [
            patch("web.servidor.REPORTES_LOCALES", self.dir / "reportes.json"),
            patch("web.servidor.DIR_EVIDENCIAS", self.dir / "evidencias"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_territorio_medellin(self):
        res = self.client.get("/api/territorio?lat=6.25&lng=-75.58")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["dane"], "05001")

    def test_crear_multipart(self):
        res = self.client.post(
            "/api/reportes",
            data={
                "descripcion": "Talud con erosión visible",
                "categoria": "RIESGO",
                "fecha_observacion": "2026-06-01",
                "lat": "6.25",
                "lng": "-75.58",
                "foto": (BytesIO(b"\x89PNG\r\n\x1a\n"), "ladera.png", "image/png"),
            },
        )
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertEqual(cuerpo["estado"], "EN_REVISION")
        self.assertEqual(cuerpo["ubicacion"]["dane"], "05001")
        ev = cuerpo["evidencias"][0]
        foto = self.client.get(ev["url"])
        try:
            self.assertEqual(foto.status_code, 200)
            self.assertEqual(foto.data[:4], b"\x89PNG")
        finally:
            foto.close()


if __name__ == "__main__":
    unittest.main()
