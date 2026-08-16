import csv
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import LOOKUP_MUNICIPIOS, SECOP_COLUMNAS
from modelo.constantes import MUNICIPIOS_ESPERADOS
from modelo.texto import aparece_como_nombre
from pipeline.processing.resolver import (
    aceptar_ubicacion,
    activo_en_periodo,
    cargar_indice,
    extraer_submunicipal,
    filtrar_contratos,
    mencionar_municipios,
    resolver,
    resolver_ciudad,
    resolver_fila,
)


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
            "fecha_de_firma": "2024-01-01",
            "fecha_de_inicio_del_contrato": "2024-01-02",
            "fecha_de_fin_del_contrato": "2025-12-31",
            "estado_contrato": "En ejecución",
            "valor_del_contrato": "150000000",
            "fecha_firma_norm": "2024-01-01",
            "fecha_inicio_norm": "2024-01-02",
            "fecha_fin_norm": "2025-12-31",
            "estado_normalizado": "ACTIVO",
            "valor_usable": "150000000",
        }
    )
    base.update(extra)
    return base


class TestIndice(unittest.TestCase):
    def test_lookup_tiene_125_sin_colision(self):
        indice = cargar_indice(LOOKUP_MUNICIPIOS)
        self.assertEqual(len(indice.por_dane), MUNICIPIOS_ESPERADOS)
        self.assertEqual(indice.por_dane["05001"], "MEDELLÍN")
        self.assertEqual(indice.por_clave["don matias"], ("05237",))
        self.assertEqual(len(indice.por_clave["san pedro"]), 2)


class TestTerritorio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indice = cargar_indice(LOOKUP_MUNICIPIOS)

    def test_objeto_medellin(self):
        fila = resolver_fila(
            _fila(objeto_del_contrato="Muro de contencion en Medellín", ciudad="Bello"),
            self.indice,
        )
        self.assertEqual(fila["municipio_resolucion"], "OBJETO")
        self.assertEqual(fila["municipio_dane"], "05001")
        self.assertEqual(fila["municipio_nombre"], "MEDELLÍN")

    def test_ciudad_si_el_objeto_no_nombra(self):
        fila = resolver_fila(_fila(ciudad="Bello"), self.indice)
        self.assertEqual(fila["municipio_resolucion"], "CIUDAD_ENTIDAD")
        self.assertEqual(fila["municipio_dane"], "05088")

    def test_multimunicipio_no_parte_el_valor(self):
        fila = resolver_fila(
            _fila(
                objeto_del_contrato="Obras entre Medellín y Bello",
                valor_del_contrato="200000000",
                valor_usable="200000000",
            ),
            self.indice,
        )
        self.assertEqual(fila["municipio_resolucion"], "MULTIMUNICIPIO")
        self.assertEqual(fila["municipio_dane"], "")
        self.assertIn("05001", fila["municipios_mencionados"])
        self.assertIn("05088", fila["municipios_mencionados"])
        self.assertEqual(fila["valor_del_contrato"], "200000000")
        self.assertEqual(fila["valor_usable"], "200000000")

    def test_alias_don_matias(self):
        fila = resolver_fila(
            _fila(objeto_del_contrato="Mantenimiento vial", ciudad="Don Matías"),
            self.indice,
        )
        self.assertEqual(fila["municipio_resolucion"], "CIUDAD_ENTIDAD")
        self.assertEqual(fila["municipio_dane"], "05237")

    def test_alias_santafe(self):
        dane, tipo = resolver_ciudad("Santafé De Antioquia", self.indice)
        self.assertEqual(tipo, "unico")
        self.assertEqual(dane, ["05042"])

    def test_no_definido_sin_objeto_queda_sin_resolver(self):
        fila = resolver_fila(
            _fila(objeto_del_contrato="Mantenimiento de via terciaria", ciudad="No Definido"),
            self.indice,
        )
        self.assertEqual(fila["municipio_resolucion"], "SIN_RESOLVER")
        self.assertEqual(fila["municipio_dane"], "")

    def test_san_pedro_es_ambiguo(self):
        fila = resolver_fila(
            _fila(objeto_del_contrato="Mejoramiento de via", ciudad="San Pedro"),
            self.indice,
        )
        self.assertEqual(fila["municipio_resolucion"], "AMBIGUO")
        self.assertIn("05664", fila["municipios_mencionados"])
        self.assertIn("05665", fila["municipios_mencionados"])
        self.assertEqual(fila["municipio_dane"], "")

    def test_san_pedro_completo_no_es_ambiguo(self):
        unicos, ambiguos = mencionar_municipios(
            "Obras en San Pedro de los Milagros",
            self.indice,
        )
        self.assertEqual(unicos, ["05664"])
        self.assertEqual(ambiguos, [])

    def test_san_pedro_uraba_sin_de(self):
        unicos, ambiguos = mencionar_municipios(
            "Estacion de policia del municipio de San Pedro Uraba",
            self.indice,
        )
        self.assertEqual(unicos, ["05665"])
        self.assertEqual(ambiguos, [])

    def test_bello_no_pega_en_bellota(self):
        self.assertFalse(aparece_como_nombre("Bello", "obras en bellota"))
        unicos, _ = mencionar_municipios("obras en bellota", self.indice)
        self.assertNotIn("05088", unicos)

    def test_vereda_con_fragmento(self):
        texto = "Placa huella en la vereda El Rosario del municipio de Ituango"
        fila = resolver_fila(_fila(objeto_del_contrato=texto, ciudad="Ituango"), self.indice)
        self.assertEqual(fila["municipio_dane"], "05361")
        self.assertIn("vereda", fila["ubicacion_submunicipal"])
        self.assertIn("El Rosario", fila["ubicacion_fragmento"])
        self.assertTrue(aceptar_ubicacion(fila["ubicacion_fragmento"], texto))
        self.assertEqual(fila["ubicacion_fuente"], "objeto_del_contrato")

    def test_municipio_solo_no_es_submunicipal(self):
        lugar, fragmento, _ = extraer_submunicipal("Obras en Medellín", self.indice)
        self.assertEqual(lugar, "")
        self.assertEqual(fragmento, "")

    def test_via_terciaria_no_es_un_lugar(self):
        lugar, fragmento, _ = extraer_submunicipal(
            "Mantenimiento de via terciaria",
            self.indice,
        )
        self.assertEqual(lugar, "")
        self.assertEqual(fragmento, "")

    def test_fragmento_inventado_se_rechaza(self):
        self.assertFalse(aceptar_ubicacion("barrio Centro", "Obras de contencion en ladera"))


class TestTiempo(unittest.TestCase):
    def test_duracion_y_anio(self):
        indice = cargar_indice(LOOKUP_MUNICIPIOS)
        fila = resolver_fila(_fila(), indice)
        self.assertEqual(fila["anio_firma"], "2024")
        self.assertEqual(fila["duracion_dias"], "729")

    def test_solape_de_periodo(self):
        fila = _fila()
        self.assertTrue(activo_en_periodo(fila, date(2024, 6, 1), date(2024, 12, 31)))
        self.assertFalse(activo_en_periodo(fila, date(2026, 1, 1), date(2026, 6, 1)))

    def test_filtro_territorio_y_periodo(self):
        indice = cargar_indice(LOOKUP_MUNICIPIOS)
        filas = [
            resolver_fila(
                _fila(
                    id_contrato="A",
                    ciudad="Medellin",
                    fecha_inicio_norm="2020-01-01",
                    fecha_fin_norm="2021-01-01",
                    estado_normalizado="FINALIZADO",
                ),
                indice,
            ),
            resolver_fila(
                _fila(
                    id_contrato="B",
                    ciudad="Bello",
                    fecha_inicio_norm="2024-01-01",
                    fecha_fin_norm="2026-01-01",
                    estado_normalizado="ACTIVO",
                ),
                indice,
            ),
        ]
        hallados = filtrar_contratos(
            filas,
            dane="05088",
            desde=date(2024, 6, 1),
            hasta=date(2024, 12, 31),
            estado="activo",
        )
        self.assertEqual([f["id_contrato"] for f in hallados], ["B"])


class TestArchivo(unittest.TestCase):
    def test_escribe_csv_y_reporte(self):
        filas = [
            _fila(id_contrato="A", ciudad="Medellin"),
            _fila(id_contrato="B", ciudad="No Definido", objeto_del_contrato="Via terciaria"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            entrada = tmp / "limpio.csv"
            campos = list(filas[0].keys())
            with entrada.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=campos)
                writer.writeheader()
                writer.writerows(filas)
            resumen = resolver(
                entrada,
                salida=tmp / "resueltos.csv",
                reporte=tmp / "reporte.txt",
                manifiesto=tmp / "manifiesto.json",
            )
            self.assertEqual(resumen["filas"], 2)
            self.assertEqual(resumen["resolucion"]["CIUDAD_ENTIDAD"], 1)
            self.assertEqual(resumen["resolucion"]["SIN_RESOLVER"], 1)
            with (tmp / "resueltos.csv").open(encoding="utf-8") as fh:
                salidas = list(csv.DictReader(fh))
            self.assertEqual(salidas[0]["municipio_dane"], "05001")
            self.assertEqual(salidas[1]["municipio_resolucion"], "SIN_RESOLVER")
            texto = (tmp / "reporte.txt").read_text(encoding="utf-8")
            self.assertIn("El valor no se parte", texto)
            data = json.loads((tmp / "manifiesto.json").read_text(encoding="utf-8"))
            self.assertEqual(data["municipios_lookup"], MUNICIPIOS_ESPERADOS)


if __name__ == "__main__":
    unittest.main()
