"""IA asistida (Groq) en reportes y relaciones: sugerencias, nunca decisiones.

Cubre ia_cliente.py (el llamador compartido), reportes/ia.py (sugerir
categoría, evaluar riesgo) y relaciones/ia.py (explicar una conexión ya
sugerida por reglas). Todo mockeado — no llama a la red real.
"""

import json
import unittest
from unittest.mock import patch

import ia_cliente
from relaciones.ia import explicar_relacion
from reportes.ia import evaluar_riesgo, sugerir_categoria


class _RespuestaFalsa:
    def __init__(self, cuerpo: bytes):
        self._cuerpo = cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._cuerpo


def _cuerpo_groq(texto: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": texto}}]}).encode("utf-8")


class TestIaCliente(unittest.TestCase):
    def test_sin_clave_no_llama(self):
        with patch("ia_cliente.IA_CLAVE", None), patch("urllib.request.urlopen") as mock_urlopen:
            out = ia_cliente.llamar_ia("sistema", "usuario")
        self.assertIsNone(out)
        mock_urlopen.assert_not_called()

    def test_con_clave_devuelve_contenido(self):
        cuerpo = _cuerpo_groq("hola")
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = ia_cliente.llamar_ia("sistema", "usuario")
        self.assertEqual(out, "hola")

    def test_falla_de_red_devuelve_none(self):
        import urllib.error

        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("sin red")
        ):
            out = ia_cliente.llamar_ia("sistema", "usuario")
        self.assertIsNone(out)

    def test_extraer_json_con_texto_alrededor(self):
        out = ia_cliente.extraer_json('Aquí tienes: {"a": 1} gracias')
        self.assertEqual(out, {"a": 1})

    def test_extraer_json_invalido(self):
        self.assertIsNone(ia_cliente.extraer_json("esto no es JSON"))


class TestSugerirCategoria(unittest.TestCase):
    def test_texto_muy_corto_no_llama_ia(self):
        with patch("ia_cliente.IA_CLAVE", "clave"), patch("urllib.request.urlopen") as mock_urlopen:
            out = sugerir_categoria("corto")
        self.assertIsNone(out)
        mock_urlopen.assert_not_called()

    def test_categoria_valida_se_acepta(self):
        contenido = json.dumps({"categoria": "RIESGO", "motivo": "menciona un talud inestable"})
        cuerpo = _cuerpo_groq(contenido)
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = sugerir_categoria("Hay un talud que se ve inestable cerca de la vía principal")
        self.assertEqual(out["categoria"], "RIESGO")
        self.assertIn("talud", out["motivo"])

    def test_categoria_inventada_se_descarta(self):
        # La IA no puede colar una categoría que el modelo no reconoce.
        contenido = json.dumps({"categoria": "URGENTISIMO", "motivo": "..."})
        cuerpo = _cuerpo_groq(contenido)
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = sugerir_categoria("Una descripción cualquiera de más de quince caracteres")
        self.assertIsNone(out)

    def test_sin_clave_devuelve_none(self):
        with patch("ia_cliente.IA_CLAVE", None):
            out = sugerir_categoria("Una descripción cualquiera de más de quince caracteres")
        self.assertIsNone(out)


class TestEvaluarRiesgo(unittest.TestCase):
    def test_nivel_valido_se_acepta(self):
        contenido = json.dumps({"nivel": "ALTA", "motivo": "describe riesgo de colapso inminente"})
        cuerpo = _cuerpo_groq(contenido)
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = evaluar_riesgo("El muro de contención tiene una grieta grande y puede colapsar")
        self.assertEqual(out["nivel"], "ALTA")

    def test_nivel_inventado_se_descarta(self):
        contenido = json.dumps({"nivel": "CRITICO", "motivo": "..."})
        cuerpo = _cuerpo_groq(contenido)
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = evaluar_riesgo("Una descripción cualquiera de más de quince caracteres")
        self.assertIsNone(out)

    def test_json_invalido_cae_a_none(self):
        cuerpo = _cuerpo_groq("no es json")
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = evaluar_riesgo("Una descripción cualquiera de más de quince caracteres")
        self.assertIsNone(out)


class TestExplicarRelacion(unittest.TestCase):
    def _reporte(self):
        return {
            "categoria": "OBRA_INCONCLUSA",
            "descripcion": "El muro de contención sigue sin terminar",
            "ubicacion": {"nombre": "Puerto Berrío"},
        }

    def _contrato(self):
        return {"objeto": "Construcción de muro de contención", "municipio_nombre": "Puerto Berrío"}

    def test_sin_clave_devuelve_none(self):
        with patch("ia_cliente.IA_CLAVE", None):
            out = explicar_relacion(
                reporte=self._reporte(),
                contrato=self._contrato(),
                senales=["TERRITORIAL"],
                evidencia_reglas="Mismo municipio",
            )
        self.assertIsNone(out)

    def test_con_clave_devuelve_parrafo(self):
        cuerpo = _cuerpo_groq("Ambos hablan del mismo muro de contención en el mismo municipio.")
        with patch("ia_cliente.IA_CLAVE", "clave"), patch(
            "urllib.request.urlopen", return_value=_RespuestaFalsa(cuerpo)
        ):
            out = explicar_relacion(
                reporte=self._reporte(),
                contrato=self._contrato(),
                senales=["TERRITORIAL", "SEMANTICA"],
                evidencia_reglas="Mismo municipio; el objeto y lo observado comparten términos",
            )
        self.assertIn("muro de contención", out)


if __name__ == "__main__":
    unittest.main()
