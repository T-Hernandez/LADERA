import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from busqueda import buscar
from busqueda.consulta import validar_consulta
from busqueda.interpretar import interpretar
from config import LOOKUP_MUNICIPIOS, FIXTURE_DATOS


def _lookup():
    return json.loads(LOOKUP_MUNICIPIOS.read_text(encoding="utf-8"))


def _datos():
    return json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))


class TestInterpretar(unittest.TestCase):
    def test_ejemplo_terminaron_inconclusas(self):
        out = interpretar(
            "Muéstrame contratos que terminaron el año pasado y tienen reportes de obras inconclusas",
            _lookup(),
            hoy=date(2026, 8, 15),
        )
        f = out["filtros"]
        self.assertEqual(out["metodo"], "REGLAS")
        self.assertEqual(f["estado_contrato"], "FINALIZADO")
        self.assertEqual(f["categoria_reporte"], "OBRA_INCONCLUSA")
        self.assertTrue(f["con_reportes"])
        self.assertEqual(f["periodo"]["desde"], "2025-01-01")
        self.assertEqual(f["periodo"]["hasta"], "2025-12-31")
        self.assertFalse(f["texto"])

    def test_ejemplo_esta_zona(self):
        out = interpretar(
            "¿Qué contratos hay relacionados con esta zona?",
            _lookup(),
            dane_zona="05001",
        )
        self.assertEqual(out["filtros"]["territorio_dane"], "05001")
        self.assertTrue(out["filtros"]["con_relacion"])
        self.assertFalse(out["filtros"]["texto"])

    def test_ejemplo_riesgo(self):
        out = interpretar(
            "Obras de mitigación de riesgo que siguen teniendo reportes ciudadanos",
            _lookup(),
        )
        f = out["filtros"]
        self.assertEqual(f["categoria_reporte"], "RIESGO")
        self.assertTrue(f["con_reportes"])
        self.assertEqual(f["estado_contrato"], "ACTIVO")


class TestEjecutar(unittest.TestCase):
    def test_popular_trae_contrato_y_reporte(self):
        out = buscar("Popular", _datos(), _lookup(), usar_ia=False)
        ids_c = {c["id"] for c in out["contratos"]}
        ids_r = {r["id"] for r in out["reportes"]}
        self.assertIn("FIX-X", ids_c)
        self.assertIn("REP-1", ids_r)
        self.assertTrue(out["fuentes"])
        self.assertEqual(out["interpretacion"]["ia"], "apagada")
        self.assertIn("no significa cero inversión", out["nota"])

    def test_zona_medellin_relacionados(self):
        out = buscar(
            "¿Qué contratos hay relacionados con esta zona?",
            _datos(),
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        self.assertIn("FIX-X", ids_c)
        self.assertNotIn("FIX-Y", ids_c)
        self.assertEqual(out["filtros"]["territorio_dane"], "05001")

    def test_ia_no_puede_colar_resultados(self):
        with self.assertRaises(ValueError):
            validar_consulta({"contratos": [{"id": "inventado"}]})

    def test_sin_ia_sigue_funcionando(self):
        from unittest.mock import patch

        with patch("busqueda.ia.IA_CLAVE", None), patch("busqueda.ia.IA_URL", None):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        ids_r = {r["id"] for r in out["reportes"]}
        self.assertIn("REP-2", ids_r)

    def test_cero_coincidencias_sigue_inspeccionable(self):
        out = buscar(
            "Muéstrame contratos que terminaron el año pasado y tienen reportes de obras inconclusas",
            _datos(),
            _lookup(),
            hoy=date(2026, 8, 15),
            usar_ia=False,
        )
        self.assertEqual(out["filtros"]["periodo"]["desde"], "2025-01-01")
        self.assertEqual(out["contratos"], [])
        self.assertIn("filtros", out)
        self.assertIn("fuentes", out)
        self.assertIn("no significa cero inversión", out["nota"])


class _RespuestaFalsa:
    def __init__(self, cuerpo: bytes):
        self._cuerpo = cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._cuerpo


class TestIA(unittest.TestCase):
    """interpretar_con_ia: éxito, JSON inválido y fallo de red caen todos a REGLAS."""

    def _con_clave(self):
        return patch("busqueda.ia.IA_CLAVE", "clave-de-prueba"), patch("busqueda.ia.IA_URL", "https://ia.local/chat")

    def test_ia_exitosa_se_usa(self):
        p1, p2 = self._con_clave()
        contenido = json.dumps({"territorio_dane": "05001", "estado_contrato": "ACTIVO"})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("contratos activos en Medellín", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "IA")
        self.assertEqual(out["interpretacion"]["ia"], "usada")
        self.assertEqual(out["filtros"]["territorio_dane"], "05001")

    def test_ia_json_invalido_cae_a_reglas(self):
        p1, p2 = self._con_clave()
        cuerpo = json.dumps({"choices": [{"message": {"content": "esto no es JSON"}}]}).encode("utf-8")
        with p1, p2, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertIn("fallo", out["interpretacion"]["ia"])

    def test_ia_campo_no_permitido_cae_a_reglas(self):
        p1, p2 = self._con_clave()
        contenido = json.dumps({"contratos": [{"id": "inventado"}]})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")

    def test_ia_falla_de_red_cae_a_reglas(self):
        import urllib.error

        p1, p2 = self._con_clave()
        with p1, p2, patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sin red")):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertIn("fallo", out["interpretacion"]["ia"])


class TestApi(unittest.TestCase):
    def test_buscar_inspeccionable(self):
        from web.servidor import app

        client = app.test_client()
        patcher = patch("web.servidor.DATOS_FINAL", Path("no-existe.json"))
        patcher.start()
        self.addCleanup(patcher.stop)
        res = client.post("/api/buscar", json={"pregunta": "Popular", "usar_ia": False})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        cuerpo = res.get_json()
        self.assertIn("filtros", cuerpo)
        self.assertIn("contratos", cuerpo)
        self.assertIn("reportes", cuerpo)
        self.assertIn("fuentes", cuerpo)
        self.assertTrue(any(f.get("id") == "FIX-X" for f in cuerpo["fuentes"]))


if __name__ == "__main__":
    unittest.main()
