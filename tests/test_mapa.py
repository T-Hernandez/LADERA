import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS
from mapa.capas import contrato_en_anio, recorte_territorial
from modelo import MUNICIPIOS_ESPERADOS


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestRecorte(unittest.TestCase):
    def test_siempre_125_municipios(self):
        recorte = recorte_territorial(_datos())
        self.assertEqual(len(recorte["municipios"]), MUNICIPIOS_ESPERADOS)
        self.assertIn("no significa cero inversión", recorte["nota"])
        self.assertIn("no demuestra causa", recorte["nota"])

    def test_medellin_2026_tiene_contrato_dinero_y_reporte(self):
        recorte = recorte_territorial(_datos(), anio=2026)
        snap = recorte["municipios"]["05001"]
        self.assertEqual(snap["contratos"], 1)
        self.assertEqual(snap["activos"], 1)
        self.assertEqual(snap["finalizados"], 0)
        self.assertEqual(snap["plata"], 2400000000)
        self.assertEqual(snap["reportes"], 1)
        self.assertEqual(snap["relaciones_sugeridas"], 1)
        self.assertEqual(snap["contratos_relacionados"], 0)
        self.assertIn("FIX-X", snap["contrato_ids"])
        self.assertIn("REP-1", snap["reporte_ids"])

    def test_medellin_2024_tiene_contrato_sin_reporte(self):
        recorte = recorte_territorial(_datos(), anio=2024)
        snap = recorte["municipios"]["05001"]
        self.assertEqual(snap["contratos"], 1)
        self.assertEqual(snap["contrato_ids"], ["FIX-Z"])
        self.assertEqual(snap["reportes"], 0)
        self.assertEqual(snap["plata"], 0)
        self.assertEqual(snap["sin_cifra"], 1)
        self.assertEqual(snap["relaciones_sugeridas"], 0)

    def test_bello_2024_finalizado(self):
        recorte = recorte_territorial(_datos(), anio=2024, estado="FINALIZADO")
        snap = recorte["municipios"]["05088"]
        self.assertEqual(snap["contratos"], 1)
        self.assertEqual(snap["finalizados"], 1)
        self.assertEqual(snap["plata"], 890000000)
        self.assertEqual(recorte["municipios"]["05001"]["contratos"], 0)

    def test_ituango_2026_reporte_sin_contrato(self):
        recorte = recorte_territorial(_datos(), anio=2026)
        snap = recorte["municipios"]["05361"]
        self.assertEqual(snap["contratos"], 0)
        self.assertEqual(snap["reportes"], 1)
        self.assertEqual(snap["plata"], 0)

    def test_activo_deja_fuera_lo_finalizado(self):
        recorte = recorte_territorial(_datos(), estado="ACTIVO")
        self.assertIn("FIX-X", recorte["municipios"]["05001"]["contrato_ids"])
        self.assertEqual(recorte["municipios"]["05088"]["contratos"], 0)

    def test_vigencia_cruza_anios(self):
        self.assertTrue(
            contrato_en_anio(
                {"fecha_inicio": "2025-04-01", "fecha_fin": "2026-11-30", "fecha_firma": "2025-03-12"},
                2026,
            )
        )
        self.assertFalse(
            contrato_en_anio(
                {"fecha_inicio": "2025-04-01", "fecha_fin": "2026-11-30", "fecha_firma": "2025-03-12"},
                2024,
            )
        )


class TestApi(unittest.TestCase):
    def test_mapa_medellin(self):
        from web.servidor import app

        client = app.test_client()
        patcher = patch("web.servidor.DATOS_FINAL", Path("no-existe.json"))
        patcher.start()
        self.addCleanup(patcher.stop)
        res = client.get("/api/mapa?anio=2026")
        self.assertEqual(res.status_code, 200)
        cuerpo = res.get_json()
        self.assertEqual(cuerpo["municipios"]["05001"]["reportes"], 1)
        self.assertEqual(cuerpo["filtro"]["anio"], 2026)


if __name__ == "__main__":
    unittest.main()
