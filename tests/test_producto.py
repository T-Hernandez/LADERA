import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS
from producto.recorrido import armar_recorrido


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestRecorrido(unittest.TestCase):
    def test_sin_zona_pide_buscarla(self):
        hilo = armar_recorrido(_datos())
        self.assertEqual(hilo["siguiente"], "zona")
        self.assertFalse(hilo["pasos"][1]["listo"])

    def test_medellin_2026_es_un_hilo(self):
        hilo = armar_recorrido(_datos(), "05001", anio=2026, pregunta="muro inconcluso en El Popular")
        self.assertEqual(hilo["zona"]["dane"], "05001")
        self.assertIn("FIX-X", hilo["contrato_ids"])
        self.assertIn("REP-1", hilo["reporte_ids"])
        self.assertTrue(hilo["relacion_ids"])
        self.assertEqual(hilo["siguiente"], "continuar")
        self.assertTrue(hilo["pasos"][2]["listo"])
        self.assertTrue(hilo["pasos"][4]["listo"])
        self.assertIn("no significa cero inversión", hilo["nota"])
        self.assertIn("ni declara irregularidad", hilo["nota"])

    def test_bello_tiene_contratos_y_pide_evidencia(self):
        hilo = armar_recorrido(_datos(), "05088")
        self.assertTrue(hilo["contrato_ids"])
        self.assertEqual(hilo["reporte_ids"], [])
        self.assertEqual(hilo["siguiente"], "evidencia")

    def test_ituango_tiene_reporte_sin_relacion(self):
        hilo = armar_recorrido(_datos(), "05361")
        self.assertIn("REP-2", hilo["reporte_ids"])
        self.assertEqual(hilo["relacion_ids"], [])
        self.assertEqual(hilo["siguiente"], "relaciones")

    def test_descartado_no_entra_al_hilo(self):
        datos = _datos()
        datos["reportes"]["REP-2"]["estado"] = "DESCARTADO"
        hilo = armar_recorrido(datos, "05361")
        self.assertNotIn("REP-2", hilo["reporte_ids"])


class TestApi(unittest.TestCase):
    def test_recorrido_medellin(self):
        from web.servidor import app

        client = app.test_client()
        patcher = patch("web.servidor.DATOS_FINAL", Path("no-existe.json"))
        patcher.start()
        self.addCleanup(patcher.stop)
        res = client.get("/api/recorrido?dane=05001&anio=2026")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertIn("FIX-X", cuerpo["contrato_ids"])
        self.assertEqual(len(cuerpo["pasos"]), 8)
        self.assertEqual(client.get("/api/salud").get_json()["fase"], 13)


if __name__ == "__main__":
    unittest.main()
