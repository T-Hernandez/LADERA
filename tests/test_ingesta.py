import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pipeline.ingestion.bajar import IngestaError, aplanar, descargar, leer_pagina


def _fila(i: int) -> dict:
    return {
        "id_contrato": f"CO1.PCCNTR.{i}",
        "objeto_del_contrato": f"Obra {i}",
        "nombre_entidad": "Municipio",
        "ciudad": "Medellín",
        "departamento": "Antioquia",
        "tipo_de_contrato": "Obra",
        "fecha_de_firma": "2022-01-01T00:00:00.000",
        "fecha_de_inicio_del_contrato": "2022-01-02T00:00:00.000",
        "fecha_de_fin_del_contrato": "2022-12-31T00:00:00.000",
        "estado_contrato": "En ejecución",
        "valor_del_contrato": "1000",
        "proveedor_adjudicado": "Consorcio",
        "urlproceso": {"url": f"https://community.secop.gov.co/Public/Tendering/{i}"},
        "proceso_de_compra": f"CO1.BDOS.{i}",
        "referencia_del_contrato": f"REF-{i}",
    }


class TestAplanar(unittest.TestCase):
    def test_urlproceso_sale_plana(self):
        plano = aplanar(_fila(1))
        self.assertEqual(
            plano["urlproceso"],
            "https://community.secop.gov.co/Public/Tendering/1",
        )
        self.assertNotIsInstance(plano["urlproceso"], dict)


class TestLeerPagina(unittest.TestCase):
    def test_http_error_se_detiene(self):
        def obtener(url, timeout, token):
            return 500, "boom"

        with self.assertRaises(IngestaError):
            leer_pagina(0, 2, "x=1", obtener, 5, None)

    def test_json_corrupto_se_detiene(self):
        def obtener(url, timeout, token):
            return 200, "<html>no"

        with self.assertRaises(IngestaError):
            leer_pagina(0, 2, "x=1", obtener, 5, None)

    def test_sin_id_se_detiene(self):
        def obtener(url, timeout, token):
            return 200, json.dumps([{"objeto_del_contrato": "sin id"}])

        with self.assertRaises(IngestaError):
            leer_pagina(0, 2, "x=1", obtener, 5, None)


class TestDescargar(unittest.TestCase):
    def test_pagina_y_guarda_manifiesto(self):
        paginas = {
            0: [_fila(1), _fila(2)],
            2: [_fila(3)],
        }

        def obtener(url, timeout, token):
            if "offset=0" in url:
                return 200, json.dumps(paginas[0])
            if "offset=2" in url:
                return 200, json.dumps(paginas[2])
            return 200, "[]"

        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "contratos_2026-08-15.csv"
            manifiesto = Path(tmp) / "ingestion_manifest.json"
            entrada = descargar(
                obtener=obtener,
                limit=2,
                destino=destino,
                manifiesto=manifiesto,
            )
            self.assertEqual(entrada["estado"], "OK")
            self.assertEqual(entrada["cantidad_descargada"], 3)
            self.assertEqual(entrada["hash"], _sha(destino))
            with destino.open(encoding="utf-8") as fh:
                filas = list(csv.DictReader(fh))
            self.assertEqual(len(filas), 3)
            self.assertTrue(filas[0]["urlproceso"].startswith("https://community.secop.gov.co"))
            doc = json.loads(manifiesto.read_text(encoding="utf-8"))
            self.assertEqual(doc["actual"]["cantidad_descargada"], 3)
            self.assertIn("where", doc["actual"]["consulta"])

    def test_no_sobrescribe(self):
        def obtener(url, timeout, token):
            return 200, json.dumps([_fila(1)])

        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "contratos_2026-08-15.csv"
            manifiesto = Path(tmp) / "ingestion_manifest.json"
            destino.write_text("ya existia\n", encoding="utf-8")
            with self.assertRaises(IngestaError):
                descargar(obtener=obtener, destino=destino, manifiesto=manifiesto)
            self.assertEqual(destino.read_text(encoding="utf-8"), "ya existia\n")

    def test_error_no_deja_csv_final(self):
        def obtener(url, timeout, token):
            return 503, "ocupado"

        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "contratos_2026-08-15.csv"
            manifiesto = Path(tmp) / "ingestion_manifest.json"
            with self.assertRaises(IngestaError):
                descargar(obtener=obtener, destino=destino, manifiesto=manifiesto)
            self.assertFalse(destino.exists())
            doc = json.loads(manifiesto.read_text(encoding="utf-8"))
            self.assertIsNone(doc["actual"])
            self.assertEqual(doc["historial"][0]["estado"], "FALLO")

    def test_cero_filas_falla(self):
        def obtener(url, timeout, token):
            return 200, "[]"

        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "contratos_2026-08-15.csv"
            manifiesto = Path(tmp) / "ingestion_manifest.json"
            with self.assertRaises(IngestaError):
                descargar(obtener=obtener, destino=destino, manifiesto=manifiesto)
            self.assertFalse(destino.exists())


def _sha(ruta: Path) -> str:
    import hashlib

    return hashlib.sha256(ruta.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
