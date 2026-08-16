import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS, LOOKUP_MUNICIPIOS
from modelo import (
    MUNICIPIOS_ESPERADOS,
    ModeloInvalido,
    contrato,
    municipios_desde_lookup,
    relacion,
    reporte,
    validar_conjunto,
)


def _lookup():
    return json.loads(LOOKUP_MUNICIPIOS.read_text(encoding="utf-8"))


def _base_contrato(**extra):
    campos = dict(
        id="C-1",
        fuente="fixture",
        url_fuente="https://community.secop.gov.co/Public/Tendering/x",
        objeto="Obras de contención en el barrio Centro",
        entidad="Alcaldía",
        contratista=None,
        valor=100,
        valor_motivo=None,
        fecha_firma="2024-01-01",
        fecha_inicio="2024-01-02",
        fecha_fin="2024-12-31",
        estado="ACTIVO",
        municipio_dane="05001",
        municipio_nombre="MEDELLÍN",
        ubicaciones=[],
        texto_original="Obras de contención en el barrio Centro",
        municipios_validos={"05001", "05088"},
    )
    campos.update(extra)
    return contrato(**campos)


def _base_reporte(**extra):
    campos = dict(
        id="R-1",
        fecha_creacion="2026-01-01T00:00:00Z",
        fecha_observacion="2026-01-01",
        descripcion="El muro sigue inconcluso",
        categoria="OBRA_INCONCLUSA",
        estado="PUBLICADO",
        autor="vecina",
        ubicacion={"dane": "05001", "nombre": "MEDELLÍN", "detalle": None, "lat": None, "lng": None},
        evidencias=[],
        municipios_validos={"05001", "05088"},
    )
    campos.update(extra)
    return reporte(**campos)


class TestEntidades(unittest.TestCase):
    def test_contrato_sin_cifra_existe_pero_no_suma(self):
        c = _base_contrato(valor=None, valor_motivo="sin cifra usable")
        self.assertIsNone(c["valor"])
        self.assertEqual(c["valor_motivo"], "sin cifra usable")

    def test_valor_nulo_sin_motivo_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_contrato(valor=None, valor_motivo=None)

    def test_estados_de_confianza_se_aceptan(self):
        self.assertEqual(_base_reporte(estado="BORRADOR")["estado"], "BORRADOR")
        self.assertEqual(_base_reporte(estado="RETIRADO")["estado"], "RETIRADO")

    def test_municipio_inventado_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_contrato(municipio_dane="99999")

    def test_fragmento_ajeno_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_contrato(
                ubicaciones=[
                    {
                        "nombre": "vereda inventada",
                        "fragmento": "vereda que no existe en el objeto",
                        "fuente": "objeto",
                    }
                ]
            )

    def test_lat_sin_lng_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_reporte(ubicacion={
                "dane": "05001",
                "nombre": "MEDELLÍN",
                "detalle": None,
                "lat": 6.3,
                "lng": None,
            })

    def test_fecha_observacion_mal_formada_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_reporte(fecha_observacion="15/06/2026")

    def test_fragmento_literal_se_acepta(self):
        c = _base_contrato(
            ubicaciones=[
                {
                    "nombre": "barrio Centro",
                    "fragmento": "barrio Centro",
                    "fuente": "objeto",
                }
            ]
        )
        self.assertEqual(c["ubicaciones"][0]["fragmento"], "barrio Centro")

    def test_ia_no_confirma(self):
        with self.assertRaises(ModeloInvalido):
            relacion(
                id="REL-X",
                origen={"tipo": "reporte", "id": "R-1"},
                destino={"tipo": "contrato", "id": "C-1"},
                tipo_relacion="SEMANTICA",
                metodo="IA",
                estado="CONFIRMADA",
                evidencia="el modelo lo afirmó",
                creado_en="2026-01-01T00:00:00Z",
                ids_contrato={"C-1"},
                ids_reporte={"R-1"},
            )

    def test_relacion_sin_evidencia_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            relacion(
                id="REL-X",
                origen={"tipo": "reporte", "id": "R-1"},
                destino={"tipo": "contrato", "id": "C-1"},
                tipo_relacion="TERRITORIAL",
                metodo="REGLAS",
                estado="SUGERIDA",
                evidencia="   ",
                creado_en="2026-01-01T00:00:00Z",
                ids_contrato={"C-1"},
                ids_reporte={"R-1"},
            )

    def test_relacion_a_contrato_inexistente_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            relacion(
                id="REL-X",
                origen={"tipo": "reporte", "id": "R-1"},
                destino={"tipo": "contrato", "id": "NO-EXISTE"},
                tipo_relacion="TERRITORIAL",
                metodo="REGLAS",
                estado="SUGERIDA",
                evidencia="mismo municipio",
                creado_en="2026-01-01T00:00:00Z",
                ids_contrato={"C-1"},
                ids_reporte={"R-1"},
            )

    def test_relacion_sugerida_por_reglas_se_acepta(self):
        rel = relacion(
            id="REL-1",
            origen={"tipo": "reporte", "id": "R-1"},
            destino={"tipo": "contrato", "id": "C-1"},
            tipo_relacion="TERRITORIAL",
            metodo="REGLAS",
            estado="SUGERIDA",
            evidencia="mismo municipio y el objeto cita el barrio",
            creado_en="2026-01-01T00:00:00Z",
            ids_contrato={"C-1"},
            ids_reporte={"R-1"},
        )
        self.assertEqual(rel["estado"], "SUGERIDA")
        self.assertEqual(rel["metodo"], "REGLAS")

    def test_relacion_lleva_senales_reales(self):
        rel = relacion(
            id="REL-2",
            origen={"tipo": "reporte", "id": "R-1"},
            destino={"tipo": "contrato", "id": "C-1"},
            tipo_relacion="COMPUESTA",
            metodo="REGLAS",
            estado="SUGERIDA",
            evidencia="mismo municipio y periodo compatible",
            creado_en="2026-01-01T00:00:00Z",
            senales=["TERRITORIAL", "TEMPORAL"],
            ids_contrato={"C-1"},
            ids_reporte={"R-1"},
        )
        self.assertEqual(rel["senales"], ["TEMPORAL", "TERRITORIAL"])

    def test_relacion_senal_no_permitida_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            relacion(
                id="REL-3",
                origen={"tipo": "reporte", "id": "R-1"},
                destino={"tipo": "contrato", "id": "C-1"},
                tipo_relacion="TERRITORIAL",
                metodo="REGLAS",
                estado="SUGERIDA",
                evidencia="mismo municipio",
                creado_en="2026-01-01T00:00:00Z",
                senales=["INVENTADA"],
                ids_contrato={"C-1"},
                ids_reporte={"R-1"},
            )

    def test_contrato_lleva_procedencia(self):
        c = _base_contrato(valor_clase="UTILIZABLE", resolucion_territorial="OBJETO")
        self.assertEqual(c["valor_clase"], "UTILIZABLE")
        self.assertEqual(c["resolucion_territorial"], "OBJETO")

    def test_contrato_sin_procedencia_queda_en_null(self):
        c = _base_contrato()
        self.assertIsNone(c["valor_clase"])
        self.assertIsNone(c["resolucion_territorial"])

    def test_contrato_valor_clase_no_permitida_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_contrato(valor_clase="INVENTADA")

    def test_contrato_resolucion_no_permitida_se_rechaza(self):
        with self.assertRaises(ModeloInvalido):
            _base_contrato(resolucion_territorial="INVENTADA")


class TestConjunto(unittest.TestCase):
    def test_lookup_tiene_125(self):
        municipios = municipios_desde_lookup(_lookup())
        self.assertEqual(len(municipios), MUNICIPIOS_ESPERADOS)

    def test_fixture_pasa_validacion(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        limpio = validar_conjunto(datos)
        self.assertEqual(len(limpio["municipios"]), 125)
        self.assertEqual(limpio["resumen"]["contratos"], 3)
        self.assertEqual(limpio["resumen"]["contratos_con_cifra"], 2)
        self.assertEqual(limpio["resumen"]["plata_total"], 2400000000 + 890000000)
        self.assertEqual(
            limpio["resumen"]["municipios_con_contratos"]
            + limpio["resumen"]["municipios_sin_contratos"],
            125,
        )
        self.assertIn("FIX-Z", limpio["municipios"]["05001"]["contrato_ids"])
        self.assertIsNone(limpio["contratos"]["FIX-Z"]["valor"])
        self.assertEqual(limpio["relaciones"][0]["estado"], "SUGERIDA")

    def test_contar_no_es_sumar(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        limpio = validar_conjunto(datos)
        medellin = limpio["municipios"]["05001"]
        self.assertEqual(medellin["contratos"], 2)
        self.assertEqual(medellin["plata_total"], 2400000000)

    def test_faltando_un_municipio_se_rechaza(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        datos["municipios"].pop("05001")
        with self.assertRaises(ModeloInvalido):
            validar_conjunto(datos)

    def test_agregado_mentiroso_se_corrige(self):
        datos = json.loads(FIXTURE_DATOS.read_text(encoding="utf-8"))
        datos["municipios"]["05001"]["plata_total"] = 1
        datos["resumen"]["plata_total"] = 1
        limpio = validar_conjunto(datos)
        self.assertEqual(limpio["municipios"]["05001"]["plata_total"], 2400000000)
        self.assertEqual(limpio["resumen"]["plata_total"], 2400000000 + 890000000)

    def test_ia_confirmada_en_conjunto_se_rechaza(self):
        datos = copy.deepcopy(json.loads(FIXTURE_DATOS.read_text(encoding="utf-8")))
        datos["relaciones"][0]["metodo"] = "IA"
        datos["relaciones"][0]["estado"] = "CONFIRMADA"
        with self.assertRaises(ModeloInvalido):
            validar_conjunto(datos)


if __name__ == "__main__":
    unittest.main()
