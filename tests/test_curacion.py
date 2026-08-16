import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import SECOP_COLUMNAS
from pipeline.processing.curar import clasificar_valor, curar, curar_fila, normalizar_estado


def _fila(**extra) -> dict:
    base = {col: "" for col in SECOP_COLUMNAS}
    base.update(
        {
            "id_contrato": "CO1.PCCNTR.1",
            "objeto_del_contrato": "Obras de contencion en una ladera",
            "nombre_entidad": "Municipio",
            "ciudad": "Medellin",
            "departamento": "Antioquia",
            "tipo_de_contrato": "Obra",
            "fecha_de_firma": "2024-01-01T00:00:00.000",
            "fecha_de_inicio_del_contrato": "2024-01-02T00:00:00.000",
            "fecha_de_fin_del_contrato": "2026-12-31T00:00:00.000",
            "estado_contrato": "En ejecución",
            "valor_del_contrato": "150000000",
            "urlproceso": "https://community.secop.gov.co/Public/Tendering/1",
        }
    )
    base.update(extra)
    return base


class TestReglas(unittest.TestCase):
    def test_cero_no_suma_pero_existe(self):
        clase, usable, motivo = clasificar_valor(0, None, 10_000)
        self.assertEqual(clase, "NO_UTILIZABLE")
        self.assertIsNone(usable)
        self.assertEqual(motivo, "valor en cero")

    def test_valor_minimo_va_a_revisar(self):
        clase, usable, motivo = clasificar_valor(1, None, 10_000)
        self.assertEqual(clase, "REVISAR")
        self.assertIsNone(usable)
        self.assertIn("umbral", motivo)

    def test_no_se_estima_un_valor_raro(self):
        clase, usable, _ = clasificar_valor(1, None, 10_000)
        self.assertIsNone(usable)
        self.assertNotEqual(usable, 10_000)

    def test_estado_terminado_es_finalizado(self):
        self.assertEqual(
            normalizar_estado("terminado", date(2026, 12, 31), date(2026, 8, 15), 90),
            "FINALIZADO",
        )

    def test_activo_por_vencer(self):
        self.assertEqual(
            normalizar_estado("En ejecución", date(2026, 9, 1), date(2026, 8, 15), 90),
            "PROXIMO_A_VENCER",
        )

    def test_activo_sin_fin(self):
        self.assertEqual(
            normalizar_estado("Modificado", None, date(2026, 8, 15), 90),
            "SIN_FECHA_SUFICIENTE",
        )

    def test_duplicado_se_excluye_por_id(self):
        vistos: set[str] = set()
        a = curar_fila(_fila(), vistos=vistos, hoy=date(2026, 8, 15))
        b = curar_fila(_fila(), vistos=vistos, hoy=date(2026, 8, 15))
        self.assertEqual(a["destino"], "LIMPIO")
        self.assertEqual(b["destino"], "EXCLUIDO")
        self.assertEqual(b["motivo_destino"], "id_contrato duplicado")

    def test_prueba_se_excluye(self):
        fila = curar_fila(
            _fila(objeto_del_contrato="PRUEBA", valor_del_contrato="120"),
            vistos=set(),
            hoy=date(2026, 8, 15),
        )
        self.assertEqual(fila["destino"], "EXCLUIDO")
        self.assertEqual(fila["motivo_destino"], "objeto de prueba")


class TestArchivo(unittest.TestCase):
    def test_tres_destinos_y_reporte(self):
        filas = [
            _fila(id_contrato="A", valor_del_contrato="200000"),
            _fila(id_contrato="B", valor_del_contrato="0"),
            _fila(id_contrato="C", valor_del_contrato="1", objeto_del_contrato="Muro de contencion"),
            _fila(id_contrato="D", objeto_del_contrato="prueba", valor_del_contrato="120"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            entrada = tmp / "crudo.csv"
            with entrada.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(SECOP_COLUMNAS))
                writer.writeheader()
                writer.writerows(filas)
            resumen = curar(
                entrada,
                limpio=tmp / "limpio.csv",
                revisar=tmp / "revisar.csv",
                excluidos=tmp / "excluidos.csv",
                reporte=tmp / "reporte.txt",
                manifiesto=tmp / "manifiesto.json",
                hoy=date(2026, 8, 15),
            )
            self.assertEqual(resumen["LIMPIO"], 2)
            self.assertEqual(resumen["REVISAR"], 1)
            self.assertEqual(resumen["EXCLUIDO"], 1)
            self.assertEqual(resumen["valor_utilizable"], 1)
            self.assertEqual(resumen["valor_no_utilizable"], 1)
            self.assertEqual(resumen["plata_usable"], 200000)
            with (tmp / "limpio.csv").open(encoding="utf-8") as fh:
                limpios = list(csv.DictReader(fh))
            ceros = [r for r in limpios if r["id_contrato"] == "B"]
            self.assertEqual(ceros[0]["valor_usable"], "")
            self.assertEqual(ceros[0]["valor_motivo"], "valor en cero")
            texto = (tmp / "reporte.txt").read_text(encoding="utf-8")
            self.assertIn("por qué un id no suma", texto)


if __name__ == "__main__":
    unittest.main()
