import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from busqueda import buscar
from busqueda.consulta import combinar_filtros, filtros_con_contenido, validar_consulta
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
        self.assertTrue(out["suficiente"])

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

    def test_pregunta_sin_filtros_reconocibles_no_inventa_texto(self):
        # Antes esto ponía la pregunta completa como filtro de texto y
        # devolvía 0 resultados sin explicación. Ahora se dice claramente
        # que no se identificó nada, sin inventar un filtro.
        out = interpretar("hola buenas quisiera saber por favor gracias", _lookup())
        self.assertIsNone(out["filtros"]["texto"])
        self.assertFalse(out["suficiente"])
        self.assertIn("No pude identificar filtros suficientes", out["explicacion"])

    def test_pregunta_larga_no_queda_atrapada_en_texto_estricto(self):
        # "podrían estar relacionados" son conectores, no deberían terminar
        # como palabras obligatorias de un filtro de texto.
        out = interpretar(
            "¿Qué contratos podrían estar relacionados con problemas persistentes de infraestructura?",
            _lookup(),
        )
        self.assertEqual(out["filtros"]["categoria_reporte"], "PROBLEMA_PERSISTENTE")
        texto = out["filtros"]["texto"] or ""
        self.assertNotIn("podrian", texto)
        self.assertNotIn("estar", texto)


class TestCombinarFiltros(unittest.TestCase):
    """Fase 1: la IA completa lo que las reglas no vieron; nunca lo reemplaza en silencio."""

    def test_ia_no_borra_filtros_detectados_por_reglas(self):
        reglas = {
            "territorio": "MEDELLÍN",
            "territorio_dane": "05001",
            "estado_contrato": "ACTIVO",
            "categoria_reporte": None,
            "periodo": {"desde": "2025-01-01", "hasta": "2025-12-31"},
            "con_reportes": True,
            "con_relacion": False,
            "texto": None,
        }
        ia = {"territorio_dane": "05001", "estado_contrato": "ACTIVO"}
        combinado, conflictos = combinar_filtros(reglas, ia)
        self.assertEqual(combinado["periodo"], reglas["periodo"])
        self.assertTrue(combinado["con_reportes"])
        self.assertEqual(conflictos, [])

    def test_ia_completa_lo_que_reglas_no_detecto(self):
        reglas = {
            "territorio": None,
            "territorio_dane": None,
            "estado_contrato": None,
            "categoria_reporte": None,
            "periodo": None,
            "con_reportes": False,
            "con_relacion": False,
            "texto": None,
        }
        ia = {"territorio_dane": "05001", "territorio": "MEDELLÍN", "estado_contrato": "ACTIVO"}
        combinado, conflictos = combinar_filtros(reglas, ia)
        self.assertEqual(combinado["territorio_dane"], "05001")
        self.assertEqual(combinado["estado_contrato"], "ACTIVO")
        self.assertEqual(conflictos, [])

    def test_conflicto_explicito_gana_reglas(self):
        reglas = {
            "territorio": None,
            "territorio_dane": None,
            "estado_contrato": None,
            "categoria_reporte": None,
            "periodo": {"desde": "2025-01-01", "hasta": "2025-12-31"},
            "con_reportes": False,
            "con_relacion": False,
            "texto": None,
        }
        ia = {"periodo": {"desde": "2024-01-01", "hasta": "2024-12-31"}}
        combinado, conflictos = combinar_filtros(reglas, ia)
        self.assertEqual(combinado["periodo"], reglas["periodo"])
        self.assertIn("periodo", conflictos)

    def test_filtros_con_contenido(self):
        self.assertFalse(filtros_con_contenido(validar_consulta({})))
        self.assertTrue(filtros_con_contenido(validar_consulta({"texto": "vías"})))


class TestEjecutar(unittest.TestCase):
    def test_popular_trae_contrato_y_reporte(self):
        out = buscar("Popular", _datos(), _lookup(), usar_ia=False)
        ids_c = {c["id"] for c in out["contratos"]}
        ids_r = {r["id"] for r in out["reportes"]}
        self.assertIn("FIX-X", ids_c)
        self.assertIn("REP-1", ids_r)
        self.assertTrue(out["fuentes"])
        self.assertEqual(out["interpretacion"]["ia"], "no_configurada")
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

    def test_sin_ia_configurada_sigue_funcionando(self):
        with patch("busqueda.IA_CLAVE", None), patch("busqueda.IA_URL", None):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertEqual(out["interpretacion"]["ia"], "no_configurada")
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


class TestConReportesVsConRelacion(unittest.TestCase):
    """Fase 2: con_reportes = contexto territorial/temporal; con_relacion = relación registrada."""

    def test_con_reportes_no_exige_relacion_existente(self):
        datos = copy.deepcopy(_datos())
        datos["relaciones"] = []  # sin ninguna relación registrada
        out = buscar(
            "contratos con reportes ciudadanos",
            datos,
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        # FIX-X y REP-1 siguen en el mismo municipio y periodo compatible,
        # aunque no exista ninguna relación guardada.
        self.assertIn("FIX-X", ids_c)

    def test_con_relacion_si_exige_relacion_registrada(self):
        datos = copy.deepcopy(_datos())
        datos["relaciones"] = []
        out = buscar(
            "¿Qué contratos hay relacionados con esta zona?",
            datos,
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        self.assertEqual(out["contratos"], [])

    def test_contrato_con_relacion_confirmada_cuenta_para_con_reportes(self):
        out = buscar(
            "contratos con reportes ciudadanos",
            _datos(),
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        self.assertIn("FIX-X", ids_c)

    def test_contrato_sin_reporte_cercano_no_cuenta(self):
        datos = copy.deepcopy(_datos())
        out = buscar(
            "contratos con reportes ciudadanos",
            datos,
            _lookup(),
            dane_zona="05088",  # Bello: FIX-Y, sin reportes ahí
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        self.assertNotIn("FIX-Y", ids_c)

    def test_varios_reportes_uno_solo_cerca_del_contrato(self):
        datos = copy.deepcopy(_datos())
        datos["relaciones"] = []
        # Un segundo reporte, lejos en el tiempo, no debería contar para FIX-X.
        lejano = copy.deepcopy(datos["reportes"]["REP-1"])
        lejano["id"] = "REP-LEJANO"
        lejano["fecha_observacion"] = "2015-01-01"
        datos["reportes"]["REP-LEJANO"] = lejano
        out = buscar(
            "contratos con reportes ciudadanos",
            datos,
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_r = {r["id"] for r in out["reportes"]}
        self.assertIn("REP-1", ids_r)
        self.assertNotIn("REP-LEJANO", ids_r)

    def test_reporte_descartado_no_cuenta_para_con_reportes(self):
        datos = copy.deepcopy(_datos())
        datos["relaciones"] = []
        datos["reportes"]["REP-1"]["estado"] = "DESCARTADO"
        out = buscar(
            "contratos con reportes ciudadanos",
            datos,
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        self.assertNotIn("FIX-X", ids_c)

    def test_reporte_retirado_no_cuenta_para_con_reportes(self):
        datos = copy.deepcopy(_datos())
        datos["relaciones"] = []
        datos["reportes"]["REP-1"]["estado"] = "RETIRADO"
        out = buscar(
            "contratos con reportes ciudadanos",
            datos,
            _lookup(),
            dane_zona="05001",
            usar_ia=False,
        )
        ids_c = {c["id"] for c in out["contratos"]}
        self.assertNotIn("FIX-X", ids_c)


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
    """interpretar_con_ia: éxito, combinación, conflicto, JSON inválido y fallo de red."""

    def _con_clave(self):
        # Hay que parchar el nombre en los dos módulos donde se importó:
        # busqueda/ia.py lo usa para llamar, busqueda/__init__.py lo usa
        # para decidir si siquiera intenta.
        return (
            patch("busqueda.ia.IA_CLAVE", "clave-de-prueba"),
            patch("busqueda.ia.IA_URL", "https://ia.local/chat"),
            patch("busqueda.IA_CLAVE", "clave-de-prueba"),
            patch("busqueda.IA_URL", "https://ia.local/chat"),
        )

    def test_ia_no_configurada_no_se_intenta(self):
        with patch("busqueda.IA_CLAVE", None), patch("busqueda.IA_URL", None):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertEqual(out["interpretacion"]["ia"], "no_configurada")

    def test_ia_exitosa_se_combina_con_reglas(self):
        p1, p2, p3, p4 = self._con_clave()
        contenido = json.dumps({"territorio_dane": "05001", "estado_contrato": "ACTIVO"})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, p3, p4, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("contratos activos en Medellín", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS+IA")
        self.assertEqual(out["interpretacion"]["ia"], "usada")
        self.assertEqual(out["filtros"]["territorio_dane"], "05001")

    def test_ia_no_puede_borrar_periodo_detectado_por_reglas(self):
        p1, p2, p3, p4 = self._con_clave()
        # La IA solo devuelve territorio; el periodo lo detectaron las reglas
        # a partir de "2025" en la pregunta y no debe perderse.
        contenido = json.dumps({"territorio_dane": "05001"})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, p3, p4, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("contratos de 2025 en Medellín", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["filtros"]["periodo"]["desde"], "2025-01-01")

    def test_conflicto_reglas_ia_gana_reglas(self):
        p1, p2, p3, p4 = self._con_clave()
        contenido = json.dumps({"periodo": {"desde": "2024-01-01", "hasta": "2024-12-31"}})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, p3, p4, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("contratos de 2025", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["filtros"]["periodo"]["desde"], "2025-01-01")
        self.assertIn("periodo", out["interpretacion"]["conflictos"])

    def test_ia_json_invalido_cae_a_reglas(self):
        p1, p2, p3, p4 = self._con_clave()
        cuerpo = json.dumps({"choices": [{"message": {"content": "esto no es JSON"}}]}).encode("utf-8")
        with p1, p2, p3, p4, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertEqual(out["interpretacion"]["ia"], "fallo")

    def test_ia_campo_no_permitido_cae_a_reglas(self):
        p1, p2, p3, p4 = self._con_clave()
        contenido = json.dumps({"contratos": [{"id": "inventado"}]})
        cuerpo = json.dumps({"choices": [{"message": {"content": contenido}}]}).encode("utf-8")
        with p1, p2, p3, p4, patch("urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")

    def test_ia_falla_de_red_cae_a_reglas(self):
        import urllib.error

        p1, p2, p3, p4 = self._con_clave()
        with p1, p2, p3, p4, patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sin red")):
            out = buscar("Ituango", _datos(), _lookup(), usar_ia=True)
        self.assertEqual(out["interpretacion"]["metodo"], "REGLAS")
        self.assertEqual(out["interpretacion"]["ia"], "fallo")


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
