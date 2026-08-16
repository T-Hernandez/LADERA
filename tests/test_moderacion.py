import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS, GEOJSON_MUNICIPIOS, LOOKUP_MUNICIPIOS
from mapa.capas import recorte_territorial
from reportes.almacen import ReporteError, crear_observacion
from reportes.confianza import (
    explicar_estado,
    retirar_reporte,
    revisar_reporte,
    senalar_reporte,
)
from reportes.contenido import rechazo_contenido


def _lookup():
    return json.loads(LOOKUP_MUNICIPIOS.read_text(encoding="utf-8"))


def _geojson():
    return json.loads(GEOJSON_MUNICIPIOS.read_text(encoding="utf-8"))


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestContenido(unittest.TestCase):
    def test_observacion_pasa(self):
        self.assertIsNone(rechazo_contenido("El muro sigue a medias y hay escorrentia"))

    def test_ruido_se_rechaza(self):
        self.assertIsNotNone(rechazo_contenido("asdf"))
        self.assertIsNotNone(rechazo_contenido("aaaaaaaaaa"))
        self.assertIsNotNone(rechazo_contenido("https://ejemplo.com/x"))


class TestDecisiones(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.ruta = self.dir / "reportes.json"
        self.fotos = self.dir / "evidencias"
        self.auditoria = self.dir / "auditoria.json"
        self.decisiones = self.dir / "decisiones.json"

    def _crear(self, extra=None, ahora=None, actor="local"):
        cuerpo = {
            "descripcion": "El muro sigue a medias y hay escorrentia visible",
            "categoria": "OBRA_INCONCLUSA",
            "fecha_observacion": "2026-06-15",
            "lat": 6.25,
            "lng": -75.58,
            "autor": "vecina",
        }
        if extra:
            cuerpo.update(extra)
        return crear_observacion(
            cuerpo,
            lookup=_lookup(),
            geojson=_geojson(),
            ahora=ahora or datetime(2026, 8, 15, 21, 0, tzinfo=timezone.utc),
            ruta_reportes=self.ruta,
            dir_evidencias=self.fotos,
            ruta_auditoria=self.auditoria,
            actor=actor,
        )

    def test_crear_queda_en_revision_y_se_explica(self):
        creado = self._crear()
        self.assertEqual(creado["estado"], "EN_REVISION")
        exp = explicar_estado(creado, ruta_auditoria=self.auditoria)
        self.assertIn("revisión", exp["explicacion"].casefold())
        self.assertEqual(exp["ultima"]["accion"], "CREAR")

    def test_duplicado_se_rechaza(self):
        self._crear()
        with self.assertRaises(ReporteError):
            self._crear()

    def test_frecuencia_se_rechaza(self):
        for i in range(5):
            self._crear(
                {
                    "descripcion": f"El talud {i} muestra erosión continua en la ladera norte"
                },
                actor="10.0.0.1",
            )
        with self.assertRaises(ReporteError):
            self._crear(
                {"descripcion": "Otra observación distinta sobre el mismo talud urbano"},
                actor="10.0.0.1",
            )

    def test_ia_no_verifica(self):
        creado = self._crear()
        with self.assertRaises(ReporteError):
            revisar_reporte(
                creado["id"],
                "VERIFICADO",
                "parece correcto según el modelo",
                actor="ia",
                reportes={creado["id"]: creado},
                ruta_decisiones=self.decisiones,
                ruta_auditoria=self.auditoria,
                ruta_reportes=self.ruta,
            )

    def test_revisar_deja_motivo(self):
        creado = self._crear()
        revisado = revisar_reporte(
            creado["id"],
            "DESCARTADO",
            "no describe un lugar observable",
            actor="moderación local",
            reportes={creado["id"]: creado},
            ruta_decisiones=self.decisiones,
            ruta_auditoria=self.auditoria,
            ruta_reportes=self.ruta,
        )
        self.assertEqual(revisado["estado"], "DESCARTADO")
        exp = explicar_estado(revisado, ruta_auditoria=self.auditoria)
        self.assertIn("no describe un lugar observable", exp["explicacion"])
        self.assertEqual(exp["ultima"]["resultado"], "DESCARTADO")

    def test_descartado_no_sale_en_el_mapa(self):
        datos = _datos()
        datos["reportes"]["REP-2"]["estado"] = "DESCARTADO"
        recorte = recorte_territorial(datos)
        self.assertNotIn("REP-2", recorte["municipios"]["05361"]["reporte_ids"])
        self.assertEqual(recorte["municipios"]["05361"]["reportes"], 0)

    def test_tres_senalamientos_vuelven_a_revision(self):
        datos = _datos()
        actual = datos["reportes"]["REP-2"]
        for i in range(3):
            actual = senalar_reporte(
                "REP-2",
                f"contenido irrelevante número {i} del listado",
                actor=f"vecino-{i}",
                reportes=datos["reportes"],
                ruta_decisiones=self.decisiones,
                ruta_auditoria=self.auditoria,
                ruta_reportes=self.ruta,
            )
        self.assertEqual(actual["estado"], "EN_REVISION")

    def test_retirar(self):
        creado = self._crear()
        retirado = retirar_reporte(
            creado["id"],
            "la persona ya no quiere mantenerlo visible",
            actor="vecina",
            reportes={creado["id"]: creado},
            ruta_decisiones=self.decisiones,
            ruta_auditoria=self.auditoria,
            ruta_reportes=self.ruta,
        )
        self.assertEqual(retirado["estado"], "RETIRADO")


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
            patch("web.servidor.AUDITORIA_LOCAL", self.dir / "auditoria.json"),
            patch("web.servidor.DECISIONES_REPORTES", self.dir / "decisiones.json"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_confianza_inspeccionable(self):
        res = self.client.get("/api/reportes/REP-1/confianza")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertEqual(cuerpo["estado"], "RELACIONADO")
        self.assertTrue(cuerpo["explicacion"])

    def test_revisar_y_ocultar(self):
        res = self.client.post(
            "/api/reportes/REP-2/revisar",
            json={"estado": "DESCARTADO", "motivo": "no es una observación territorial", "actor": "moderación local"},
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.get_json()["estado"], "DESCARTADO")
        mapa = self.client.get("/api/mapa").get_json()
        self.assertNotIn("REP-2", mapa["municipios"]["05361"]["reporte_ids"])
        busqueda = self.client.post("/api/buscar", json={"pregunta": "Ituango", "usar_ia": False}).get_json()
        self.assertFalse(any(r["id"] == "REP-2" for r in busqueda["reportes"]))
        confianza = self.client.get("/api/reportes/REP-2/confianza").get_json()
        self.assertIn("no es una observación territorial", confianza["explicacion"])

    def test_salud_fase_12(self):
        self.assertEqual(self.client.get("/api/salud").get_json()["fase"], 12)


if __name__ == "__main__":
    unittest.main()
