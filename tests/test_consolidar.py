import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pipeline.processing.consolidar import consolidar

CAMPOS = [
    "id_contrato",
    "objeto_del_contrato",
    "nombre_entidad",
    "urlproceso",
    "proveedor_adjudicado",
    "valor_usable",
    "valor_clase",
    "valor_motivo",
    "fecha_firma_norm",
    "fecha_inicio_norm",
    "fecha_fin_norm",
    "estado_normalizado",
    "municipio_dane",
    "municipio_nombre",
    "municipio_resolucion",
    "ubicacion_submunicipal",
    "ubicacion_fragmento",
    "ubicacion_fuente",
]


def _fila(**extra):
    base = {c: "" for c in CAMPOS}
    base.update(extra)
    return base


class TestConsolidar(unittest.TestCase):
    def _correr(self, filas):
        with tempfile.TemporaryDirectory() as tmp:
            directorio = Path(tmp)
            entrada = directorio / "resueltos.csv"
            with entrada.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=CAMPOS)
                writer.writeheader()
                writer.writerows(filas)
            salida = directorio / "datos.json"
            manifiesto = directorio / "consolidacion_manifest.json"
            resumen = consolidar(entrada, salida=salida, manifiesto=manifiesto)
            datos = json.loads(salida.read_text(encoding="utf-8"))
            return resumen, datos

    def test_objeto_y_ciudad_entidad_se_incluyen(self):
        filas = [
            _fila(
                id_contrato="C1",
                objeto_del_contrato="Obra de vías en el barrio Centro",
                nombre_entidad="Alcaldía",
                estado_normalizado="ACTIVO",
                valor_usable="1000000",
                valor_clase="UTILIZABLE",
                municipio_dane="05001",
                municipio_nombre="MEDELLÍN",
                municipio_resolucion="OBJETO",
            ),
            _fila(
                id_contrato="C2",
                objeto_del_contrato="Mantenimiento vial",
                nombre_entidad="Alcaldía de Bello",
                estado_normalizado="FINALIZADO",
                valor_usable="",
                valor_clase="NO_UTILIZABLE",
                valor_motivo="valor ausente",
                municipio_dane="05088",
                municipio_nombre="BELLO",
                municipio_resolucion="CIUDAD_ENTIDAD",
            ),
        ]
        resumen, datos = self._correr(filas)
        self.assertEqual(resumen["contratos_incluidos"], 2)
        self.assertEqual(datos["contratos"]["C1"]["valor"], 1000000)
        self.assertEqual(datos["contratos"]["C1"]["valor_clase"], "UTILIZABLE")
        self.assertEqual(datos["contratos"]["C1"]["resolucion_territorial"], "OBJETO")
        self.assertIsNone(datos["contratos"]["C2"]["valor"])
        self.assertEqual(datos["contratos"]["C2"]["valor_motivo"], "valor ausente")

    def test_multimunicipio_ambiguo_sin_resolver_quedan_fuera(self):
        filas = [
            _fila(
                id_contrato="C1",
                objeto_del_contrato="Obra en el barrio Centro",
                nombre_entidad="Alcaldía",
                estado_normalizado="ACTIVO",
                valor_usable="1000000",
                valor_clase="UTILIZABLE",
                municipio_dane="05001",
                municipio_nombre="MEDELLÍN",
                municipio_resolucion="OBJETO",
            ),
            _fila(
                id_contrato="C-MULTI",
                objeto_del_contrato="Obra entre Bello y Copacabana",
                nombre_entidad="Área Metropolitana",
                estado_normalizado="ACTIVO",
                valor_usable="500000",
                valor_clase="UTILIZABLE",
                municipio_resolucion="MULTIMUNICIPIO",
            ),
            _fila(
                id_contrato="C-AMBIGUO",
                objeto_del_contrato="Obra en San Pedro",
                nombre_entidad="Gobernación",
                estado_normalizado="ACTIVO",
                municipio_resolucion="AMBIGUO",
            ),
            _fila(
                id_contrato="C-SIN",
                objeto_del_contrato="Obra sin ciudad identificable",
                nombre_entidad="Entidad",
                estado_normalizado="DESCONOCIDO",
                municipio_resolucion="SIN_RESOLVER",
            ),
        ]
        resumen, datos = self._correr(filas)
        self.assertEqual(resumen["contratos_incluidos"], 1)
        self.assertNotIn("C-MULTI", datos["contratos"])
        self.assertNotIn("C-AMBIGUO", datos["contratos"])
        self.assertNotIn("C-SIN", datos["contratos"])
        self.assertEqual(
            resumen["excluidos_por_resolucion"],
            {"MULTIMUNICIPIO": 1, "AMBIGUO": 1, "SIN_RESOLVER": 1},
        )
        total_excluidos = sum(resumen["excluidos_por_resolucion"].values())
        self.assertEqual(total_excluidos, 3)

    def test_entidad_vacia_se_rechaza_por_el_modelo_no_se_inventa(self):
        filas = [
            _fila(
                id_contrato="C-SIN-ENTIDAD",
                objeto_del_contrato="Obra en el barrio Centro",
                nombre_entidad="",
                estado_normalizado="ACTIVO",
                municipio_dane="05001",
                municipio_nombre="MEDELLÍN",
                municipio_resolucion="OBJETO",
            ),
        ]
        resumen, datos = self._correr(filas)
        self.assertEqual(resumen["contratos_incluidos"], 0)
        self.assertEqual(len(resumen["rechazados_por_modelo"]), 1)
        self.assertEqual(resumen["rechazados_por_modelo"][0]["id"], "C-SIN-ENTIDAD")


if __name__ == "__main__":
    unittest.main()
