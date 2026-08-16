"""Construye data/fixtures/datos.json pasando por el modelo de la Fase 2."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from config import FIXTURE_DATOS, LOOKUP_MUNICIPIOS  # noqa: E402
from modelo import contrato, municipios_desde_lookup, relacion, reporte, validar_conjunto


def main() -> None:
    lookup = json.loads(LOOKUP_MUNICIPIOS.read_text(encoding="utf-8"))
    municipios = municipios_desde_lookup(lookup)
    validos = set(municipios)

    contratos = {
        "FIX-X": contrato(
            id="FIX-X",
            fuente="fixture",
            url_fuente=(
                "https://community.secop.gov.co/Public/Tendering/"
                "OpportunityDetail/Index?noticeUID=CO1.NTC.FIXTURE.X"
            ),
            objeto=(
                "Obras de contención y estabilización de ladera en el barrio "
                "El Popular, comuna 1, municipio de Medellín"
            ),
            entidad="Alcaldía de Medellín — fixture",
            contratista="Consorcio Ladera Norte (dato ficticio)",
            valor=2400000000,
            valor_motivo=None,
            fecha_firma="2025-03-12",
            fecha_inicio="2025-04-01",
            fecha_fin="2026-11-30",
            estado="ACTIVO",
            municipio_dane="05001",
            municipio_nombre="MEDELLÍN",
            ubicaciones=[
                {
                    "nombre": "barrio El Popular",
                    "fragmento": "barrio El Popular, comuna 1",
                    "fuente": "objeto",
                }
            ],
            texto_original=(
                "Obras de contención y estabilización de ladera en el barrio "
                "El Popular, comuna 1, municipio de Medellín"
            ),
            municipios_validos=validos,
        ),
        "FIX-Y": contrato(
            id="FIX-Y",
            fuente="fixture",
            url_fuente=(
                "https://community.secop.gov.co/Public/Tendering/"
                "OpportunityDetail/Index?noticeUID=CO1.NTC.FIXTURE.Y"
            ),
            objeto=(
                "Construcción de obras de drenaje y mitigación de riesgo "
                "en el sector Niquía, municipio de Bello"
            ),
            entidad="Alcaldía de Bello — fixture",
            contratista="Ingeniería del Norte S.A.S. (dato ficticio)",
            valor=890000000,
            valor_motivo=None,
            fecha_firma="2023-01-20",
            fecha_inicio="2023-02-15",
            fecha_fin="2024-06-30",
            estado="FINALIZADO",
            municipio_dane="05088",
            municipio_nombre="BELLO",
            ubicaciones=[
                {
                    "nombre": "sector Niquía",
                    "fragmento": "sector Niquía, municipio de Bello",
                    "fuente": "objeto",
                }
            ],
            texto_original=(
                "Construcción de obras de drenaje y mitigación de riesgo "
                "en el sector Niquía, municipio de Bello"
            ),
            municipios_validos=validos,
        ),
        "FIX-Z": contrato(
            id="FIX-Z",
            fuente="fixture",
            url_fuente=None,
            objeto=(
                "Mantenimiento de obras de contención en la ladera de "
                "la comuna 8, Medellín. Valor no utilizable en este fixture."
            ),
            entidad="Área Metropolitana — fixture",
            contratista=None,
            valor=None,
            valor_motivo="cifra no utilizable en el fixture",
            fecha_firma="2024-08-01",
            fecha_inicio=None,
            fecha_fin=None,
            estado="SIN_FECHA_SUFICIENTE",
            municipio_dane="05001",
            municipio_nombre="MEDELLÍN",
            ubicaciones=[],
            texto_original=(
                "Mantenimiento de obras de contención en la ladera de "
                "la comuna 8, Medellín. Valor no utilizable en este fixture."
            ),
            municipios_validos=validos,
        ),
    }

    reportes = {
        "REP-1": reporte(
            id="REP-1",
            fecha_creacion="2026-06-18T10:15:00-05:00",
            fecha_observacion="2026-06-15",
            descripcion=(
                "El muro de contención en El Popular aparece inconcluso. "
                "Hay cárcavas en el talud y escorrentía hacia las casas de abajo."
            ),
            categoria="OBRA_INCONCLUSA",
            estado="RELACIONADO",
            autor="vecina del Popular (fixture)",
            ubicacion={
                "dane": "05001",
                "nombre": "MEDELLÍN",
                "detalle": "barrio El Popular",
                "lat": 6.25,
                "lng": -75.58,
            },
            evidencias=[
                {
                    "id": "EV-1",
                    "tipo": "foto",
                    "url": "/assets/evidencia_fixture.svg",
                    "fecha": "2026-06-15",
                    "metadata": {"nota": "ilustración ficticia, no es un sitio real"},
                }
            ],
            municipios_validos=validos,
        ),
        "REP-2": reporte(
            id="REP-2",
            fecha_creacion="2026-07-02T16:40:00-05:00",
            fecha_observacion="2026-07-01",
            descripcion=(
                "Se observa un movimiento en masa sobre la vía que comunica "
                "con el casco urbano. No hay señal visible de obra reciente."
            ),
            categoria="RIESGO",
            estado="PUBLICADO",
            autor="habitante de Ituango (fixture)",
            ubicacion={
                "dane": "05361",
                "nombre": "ITUANGO",
                "detalle": "vía al casco urbano",
                "lat": 7.171,
                "lng": -76.084,
            },
            evidencias=[],
            municipios_validos=validos,
        ),
    }

    relaciones = [
        relacion(
            id="REL-1",
            origen={"tipo": "reporte", "id": "REP-1"},
            destino={"tipo": "contrato", "id": "FIX-X"},
            tipo_relacion="COMPUESTA",
            metodo="REGLAS",
            estado="SUGERIDA",
            evidencia=(
                "Mismo municipio (Medellín) y el reporte describe un muro "
                "inconcluso en El Popular, lugar citado en el objeto del contrato FIX-X."
            ),
            creado_en="2026-06-18T10:20:00-05:00",
            ids_contrato=set(contratos),
            ids_reporte=set(reportes),
        )
    ]

    datos = validar_conjunto(
        {
            "resumen": {
                "territorio": "Antioquia",
                "fuente": "fixture",
                "nota": (
                    "Datos ficticios para construir la interfaz. "
                    "No son contratos ni reportes reales."
                ),
            },
            "municipios": municipios,
            "contratos": contratos,
            "reportes": reportes,
            "relaciones": relaciones,
        }
    )

    FIXTURE_DATOS.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_DATOS.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Escrito {FIXTURE_DATOS} ({len(datos['municipios'])} municipios)")


if __name__ == "__main__":
    main()
