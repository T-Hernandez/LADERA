import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS
from escala.activar import EscalaError, estado_escala, intentar_activar
from escala.puerta import evaluar_puerta


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestPuerta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.eventos = self.dir / "eventos.json"
        self.auditoria = self.dir / "auditoria.json"

    def test_fixture_demuestra_los_cuatro_criterios(self):
        puerta = evaluar_puerta(_datos(), ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertTrue(puerta["listos"])
        self.assertFalse(puerta["puede_ensanchar"])
        self.assertFalse(puerta["autorizacion"])
        for clave in ("calidad", "utilidad", "trazabilidad", "moderacion"):
            self.assertTrue(puerta["detalle"][clave]["ok"], clave)

    def test_sin_contraste_no_hay_utilidad(self):
        datos = _datos()
        datos["relaciones"][0]["estado"] = "DESCARTADA"
        datos["reportes"]["REP-1"]["estado"] = "DESCARTADO"
        puerta = evaluar_puerta(datos, ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertFalse(puerta["detalle"]["utilidad"]["ok"])
        self.assertFalse(puerta["listos"])


class TestActivar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.kwargs = {
            "ruta_eventos": self.dir / "eventos.json",
            "ruta_auditoria": self.dir / "auditoria.json",
        }

    def test_pais_no_se_abre(self):
        with self.assertRaises(EscalaError) as ctx:
            intentar_activar("territorio", "pais", _datos(), **self.kwargs)
        self.assertIn("no se abre el país", str(ctx.exception))
        self.assertIn("co_2018", str(ctx.exception))

    def test_documentos_no_se_cablean(self):
        with self.assertRaises(EscalaError) as ctx:
            intentar_activar("fuentes", "documentos", _datos(), **self.kwargs)
        self.assertIn("documentos", str(ctx.exception))

    def test_sin_puerta_tampoco(self):
        datos = _datos()
        datos["relaciones"][0]["estado"] = "DESCARTADA"
        datos["reportes"]["REP-1"]["estado"] = "DESCARTADO"
        with self.assertRaises(EscalaError) as ctx:
            intentar_activar("territorio", "pais", datos, **self.kwargs)
        self.assertIn("no se escala solo porque es posible", str(ctx.exception))

    def test_estado_sigue_en_antioquia(self):
        estado = estado_escala(_datos(), **self.kwargs)
        self.assertEqual(estado["territorio_activo"], "Antioquia")
        self.assertEqual(estado["mapa_activo"], "municipios_antioquia.geojson")
        territorio = next(e for e in estado["ejes"] if e["id"] == "territorio")
        self.assertEqual(territorio["actual"], "departamento")
        self.assertEqual(territorio["siguiente"], "region")


class TestApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        from web.servidor import app

        self.client = app.test_client()
        self.patches = [
            patch("web.servidor.PILOTO_EVENTOS", self.dir / "eventos.json"),
            patch("web.servidor.AUDITORIA_LOCAL", self.dir / "auditoria.json"),
            patch("web.servidor.DATOS_FINAL", self.dir / "no-existe.json"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_escala_inspeccionable(self):
        res = self.client.get("/api/escala")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertEqual(len(cuerpo["ejes"]), 3)
        self.assertFalse(cuerpo["puerta"]["puede_ensanchar"])
        self.assertEqual(cuerpo["mapa_activo"], "municipios_antioquia.geojson")

    def test_activar_pais_queda_en_antioquia(self):
        res = self.client.post("/api/escala/activar", json={"eje": "territorio", "destino": "pais"})
        self.assertEqual(res.status_code, 409)
        cuerpo = res.get_json()
        self.assertIn("no se abre el país", cuerpo["error"])
        self.assertEqual(cuerpo["mapa_activo"], "municipios_antioquia.geojson")
        geo = self.client.get("/assets/municipios_antioquia.geojson")
        self.assertEqual(geo.status_code, 200)
        geo.close()


if __name__ == "__main__":
    unittest.main()
