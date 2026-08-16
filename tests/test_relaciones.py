import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS
from relaciones.almacen import fusionar_relaciones, registrar_directa, revisar_relacion
from relaciones.motor import puntuar_par, sugerir_relaciones


def _reporte(**extra) -> dict:
    base = {
        "id": "R-T",
        "fecha_observacion": "2026-06-15",
        "descripcion": "El muro de contencion en El Popular aparece inconcluso",
        "categoria": "OBRA_INCONCLUSA",
        "ubicacion": {
            "dane": "05001",
            "nombre": "MEDELLÍN",
            "detalle": "barrio El Popular",
            "lat": 6.25,
            "lng": -75.58,
        },
    }
    base.update(extra)
    return base


def _contrato(**extra) -> dict:
    base = {
        "id": "C-T",
        "objeto": (
            "Obras de contencion y estabilizacion de ladera en el barrio "
            "El Popular, comuna 1, municipio de Medellin"
        ),
        "texto_original": (
            "Obras de contencion y estabilizacion de ladera en el barrio "
            "El Popular, comuna 1, municipio de Medellin"
        ),
        "municipio_dane": "05001",
        "municipio_nombre": "MEDELLÍN",
        "fecha_inicio": "2025-04-01",
        "fecha_fin": "2026-11-30",
        "fecha_firma": "2025-03-12",
        "ubicaciones": [
            {"nombre": "barrio El Popular", "fragmento": "barrio El Popular, comuna 1"}
        ],
    }
    base.update(extra)
    return base


class TestMotor(unittest.TestCase):
    def test_compuesta_sugerida_no_confirmada(self):
        cand = puntuar_par(_reporte(), _contrato())
        self.assertIsNotNone(cand)
        self.assertEqual(cand["tipo_relacion"], "COMPUESTA")
        self.assertGreaterEqual(cand["score"], 0.5)
        self.assertIn("El Popular", cand["evidencia"])
        self.assertIn("no afirma", cand["evidencia"])

        rels = sugerir_relaciones({"R-T": _reporte()}, {"C-T": _contrato()})
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["estado"], "SUGERIDA")
        self.assertEqual(rels[0]["metodo"], "REGLAS")
        self.assertNotEqual(rels[0]["estado"], "CONFIRMADA")

    def test_otro_municipio_no_sugiere(self):
        self.assertIsNone(
            puntuar_par(_reporte(), _contrato(id="C-B", municipio_dane="05088", municipio_nombre="BELLO"))
        )

    def test_solo_mismo_municipio_no_basta(self):
        self.assertIsNone(
            puntuar_par(
                _reporte(
                    descripcion="Vi un perro en la plaza",
                    categoria="OTRO",
                    fecha_observacion="2010-01-01",
                    ubicacion={
                        "dane": "05001",
                        "nombre": "MEDELLÍN",
                        "detalle": None,
                        "lat": 6.25,
                        "lng": -75.58,
                    },
                ),
                _contrato(),
            )
        )

    def test_no_pisa_un_par_existente(self):
        existente = [
            {
                "origen": {"tipo": "reporte", "id": "R-T"},
                "destino": {"tipo": "contrato", "id": "C-T"},
            }
        ]
        rels = sugerir_relaciones(
            {"R-T": _reporte()},
            {"C-T": _contrato()},
            existentes=existente,
        )
        self.assertEqual(rels, [])

    def test_fixture_popular_con_fix_x(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        cand = puntuar_par(datos["reportes"]["REP-1"], datos["contratos"]["FIX-X"])
        self.assertIsNotNone(cand)
        self.assertEqual(cand["tipo_relacion"], "COMPUESTA")


class TestAlmacen(unittest.TestCase):
    def test_local_pisa_sugerida(self):
        suge = {
            "id": "REL-R-1",
            "origen": {"tipo": "reporte", "id": "R-T"},
            "destino": {"tipo": "contrato", "id": "C-T"},
            "estado": "SUGERIDA",
        }
        local = {**suge, "estado": "DESCARTADA", "metodo": "MANUAL"}
        fusion = fusionar_relaciones([], [local], [suge])
        self.assertEqual(fusion[0]["estado"], "DESCARTADA")

    def test_directa_confirma(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "rels.json"
            creado = registrar_directa(
                "REP-2",
                "FIX-Y",
                datos,
                ruta=ruta,
                ahora=datetime(2026, 8, 15, tzinfo=timezone.utc),
            )
            self.assertEqual(creado["tipo_relacion"], "DIRECTA")
            self.assertEqual(creado["metodo"], "DIRECTA")
            self.assertEqual(creado["estado"], "CONFIRMADA")
            self.assertNotEqual(creado["metodo"], "IA")

    def test_ia_no_confirma_al_revisar(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        ia = {
            "id": "REL-IA",
            "origen": {"tipo": "reporte", "id": "REP-1"},
            "destino": {"tipo": "contrato", "id": "FIX-X"},
            "tipo_relacion": "SEMANTICA",
            "metodo": "IA",
            "estado": "SUGERIDA",
            "evidencia": "el modelo lo afirmó",
            "creado_en": "2026-08-15T00:00:00+00:00",
        }
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "rels.json"
            with self.assertRaises(Exception) as ctx:
                revisar_relacion("REL-IA", "CONFIRMADA", "motivo de prueba con longitud suficiente", [ia], datos, ruta=ruta)
            self.assertIn("IA", str(ctx.exception))


class TestApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        from web.servidor import app

        self.client = app.test_client()
        p = patch("web.servidor.RELACIONES_LOCALES", self.dir / "relaciones.json")
        p.start()
        self.addCleanup(p.stop)
        p2 = patch("web.servidor.DATOS_FINAL", self.dir / "no-existe.json")
        p2.start()
        self.addCleanup(p2.stop)
        p3 = patch("web.servidor.MODERACION_TOKEN", "token-de-prueba")
        p3.start()
        self.addCleanup(p3.stop)

    def test_confirmar_y_etiqueta(self):
        datos = self.client.get("/api/datos").get_json()
        rel = next(r for r in datos["relaciones"] if r["id"] == "REL-1")
        self.assertEqual(rel["estado"], "SUGERIDA")
        res = self.client.post(
            "/api/relaciones/REL-1/revisar",
            json={"estado": "CONFIRMADA", "motivo": "la observación coincide con la obra descrita en el contrato"},
            headers={"X-Moderacion-Token": "token-de-prueba"},
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.get_json()["estado"], "CONFIRMADA")
        self.assertEqual(res.get_json()["metodo"], "MANUAL")
        otra = self.client.get("/api/datos").get_json()
        rel2 = next(r for r in otra["relaciones"] if r["id"] == "REL-1")
        self.assertEqual(rel2["estado"], "CONFIRMADA")

    def test_confirmar_sin_motivo_rechaza(self):
        res = self.client.post(
            "/api/relaciones/REL-1/revisar",
            json={"estado": "CONFIRMADA"},
            headers={"X-Moderacion-Token": "token-de-prueba"},
        )
        self.assertEqual(res.status_code, 400)

    def test_confirmar_relacion_deja_auditoria(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta_auditoria = Path(tmp) / "auditoria.json"
            with patch("web.servidor.AUDITORIA_LOCAL", ruta_auditoria):
                res = self.client.post(
                    "/api/relaciones/REL-1/revisar",
                    json={"estado": "CONFIRMADA", "motivo": "coincide con lo observado en el terreno"},
                    headers={"X-Moderacion-Token": "token-de-prueba"},
                )
                self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
                eventos = json.loads(ruta_auditoria.read_text(encoding="utf-8"))
                self.assertTrue(any(e["accion"] == "REVISAR_RELACION" and e["objeto"]["id"] == "REL-1" for e in eventos))

    def test_revisar_relacion_sin_token_rechaza(self):
        res = self.client.post(
            "/api/relaciones/REL-1/revisar",
            json={"estado": "CONFIRMADA"},
        )
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
