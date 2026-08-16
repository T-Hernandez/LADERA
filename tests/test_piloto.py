import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS, PILOTO_MUNICIPIOS, PILOTO_TERRITORIO
from piloto.alcance import alcance_piloto
from piloto.eventos import registrar_evento
from piloto.metricas import resumir_piloto


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestAlcance(unittest.TestCase):
    def test_sigue_siendo_antioquia(self):
        alcance = alcance_piloto()
        self.assertEqual(alcance["territorio"], PILOTO_TERRITORIO)
        self.assertEqual(alcance["municipios"], PILOTO_MUNICIPIOS)
        self.assertEqual(alcance["escala"], "piloto")
        self.assertEqual(alcance["siguiente_escala"], "region")
        self.assertIn("Antioquia", alcance["consulta_ingesta"])
        self.assertNotIn("país", alcance["consulta_ingesta"].casefold())


class TestMetricas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.eventos = self.dir / "eventos.json"
        self.auditoria = self.dir / "auditoria.json"

    def test_fixture_ya_tiene_un_contraste_util(self):
        resumen = resumir_piloto(_datos(), ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertIsNone(resumen["usuarios"])
        self.assertIn("difícil de relacionar", resumen["pregunta_central"])
        self.assertNotIn("usuarios", resumen["pregunta_central"].casefold())
        self.assertGreaterEqual(resumen["metricas"]["reportes_utiles"], 1)
        self.assertGreaterEqual(resumen["metricas"]["relaciones_sugeridas"], 1)
        self.assertEqual(resumen["metricas"]["relaciones_confirmadas"], 0)
        self.assertIn("contraste", resumen["lectura"].casefold())
        self.assertIn("no declara irregularidad", resumen["lectura"])

    def test_descartado_deja_de_ser_util(self):
        datos = _datos()
        datos["relaciones"][0]["estado"] = "DESCARTADA"
        datos["reportes"]["REP-1"]["estado"] = "DESCARTADO"
        resumen = resumir_piloto(datos, ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertEqual(resumen["metricas"]["reportes_utiles"], 0)
        self.assertIn("aún no hay", resumen["lectura"].casefold())

    def test_tiempo_hasta_encontrar(self):
        inicio = datetime(2026, 8, 15, 22, 0, tzinfo=timezone.utc)
        registrar_evento(
            accion="BUSCAR",
            sesion="s1",
            objeto={"pregunta": "Popular"},
            fecha=inicio,
            ruta=self.eventos,
        )
        registrar_evento(
            accion="CONSULTAR",
            sesion="s1",
            objeto={"tipo": "contrato", "id": "FIX-X"},
            fecha=inicio + timedelta(seconds=12),
            ruta=self.eventos,
        )
        resumen = resumir_piloto(_datos(), ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertEqual(resumen["metricas"]["busquedas_realizadas"], 1)
        self.assertEqual(resumen["metricas"]["contratos_consultados"], 1)
        self.assertEqual(resumen["metricas"]["tiempo_hasta_encontrar_segundos"]["mediana"], 12)

    def test_duplicado_se_cuenta(self):
        registrar_evento(accion="DUPLICADO", resultado="parecida", ruta=self.eventos)
        resumen = resumir_piloto(_datos(), ruta_eventos=self.eventos, ruta_auditoria=self.auditoria)
        self.assertEqual(resumen["metricas"]["reportes_duplicados"], 1)


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
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_piloto_no_cuenta_usuarios(self):
        res = self.client.get("/api/piloto")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertIsNone(cuerpo["usuarios"])
        self.assertEqual(cuerpo["alcance"]["territorio"], "Antioquia")
        self.assertEqual(cuerpo["alcance"]["municipios"], 125)
        self.assertNotIn("usuarios", json.dumps(cuerpo["metricas"]))

    def test_buscar_y_consultar_quedan_en_el_piloto(self):
        bus = self.client.post(
            "/api/buscar",
            json={"pregunta": "Popular", "usar_ia": False, "sesion": "abc"},
        )
        self.assertEqual(bus.status_code, 200, bus.get_data(as_text=True))
        ev = self.client.post(
            "/api/piloto/evento",
            json={"accion": "CONSULTAR", "sesion": "abc", "objeto": {"tipo": "contrato", "id": "FIX-X"}},
        )
        self.assertEqual(ev.status_code, 201, ev.get_data(as_text=True))
        cuerpo = self.client.get("/api/piloto").get_json()
        self.assertGreaterEqual(cuerpo["metricas"]["busquedas_realizadas"], 1)
        self.assertEqual(cuerpo["metricas"]["contratos_consultados"], 1)

    def test_salud_fase_13(self):
        self.assertEqual(self.client.get("/api/salud").get_json()["fase"], 13)


if __name__ == "__main__":
    unittest.main()
