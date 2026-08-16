"""Puente entre la Fase 5 (resuelto) y el producto: arma data/final/datos.json real.

No inventa cifra ni ubicación. Un contrato que el modelo no puede representar
(varios municipios a la vez, sin municipio resuelto, o un campo que no pasa el
contrato de modelo/entidades.py) queda fuera del mapa, con el motivo en el
manifiesto — no se fuerza a caber.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    CONSOLIDACION_MANIFIESTO,
    DATOS_FINAL,
    LOOKUP_MUNICIPIOS,
    RESOLUCION_SALIDA,
    SECOP_FUENTE,
)
from modelo import ModeloInvalido, contrato, municipios_desde_lookup, validar_conjunto  # noqa: E402

# El modelo (Fase 2) solo admite un municipio por contrato. Un MULTIMUNICIPIO
# no se le asigna al primero de la lista: se deja fuera hasta que el modelo
# admita varios. Ver Plan.md, FASE 5: "el valor no se parte".
RESOLUCIONES_USABLES = {"OBJETO", "CIUDAD_ENTIDAD"}


class ConsolidacionError(RuntimeError):
    pass


def _valor(fila: dict) -> tuple[int | None, str | None]:
    crudo = (fila.get("valor_usable") or "").strip()
    if crudo:
        return int(crudo), None
    return None, (fila.get("valor_motivo") or "sin cifra usable")


def _ubicaciones(fila: dict) -> list[dict]:
    lugar = (fila.get("ubicacion_submunicipal") or "").strip()
    fragmento = (fila.get("ubicacion_fragmento") or "").strip()
    fuente = (fila.get("ubicacion_fuente") or "").strip()
    if not (lugar and fragmento and fuente):
        return []
    return [{"nombre": lugar, "fragmento": fragmento, "fuente": fuente}]


def fila_a_contrato(fila: dict, validos: set[str]) -> dict:
    valor, valor_motivo = _valor(fila)
    texto = (fila.get("objeto_del_contrato") or "").strip()
    url = (fila.get("urlproceso") or "").strip() or None
    return contrato(
        id=fila["id_contrato"],
        fuente="secop2",
        url_fuente=url,
        objeto=texto,
        entidad=fila.get("nombre_entidad") or "",
        contratista=fila.get("proveedor_adjudicado") or None,
        valor=valor,
        valor_motivo=valor_motivo,
        fecha_firma=fila.get("fecha_firma_norm") or None,
        fecha_inicio=fila.get("fecha_inicio_norm") or None,
        fecha_fin=fila.get("fecha_fin_norm") or None,
        estado=fila.get("estado_normalizado") or "DESCONOCIDO",
        municipio_dane=fila.get("municipio_dane") or "",
        municipio_nombre=fila.get("municipio_nombre") or "",
        ubicaciones=_ubicaciones(fila),
        texto_original=texto,
        municipios_validos=validos,
    )


def consolidar(
    entrada: Path = RESOLUCION_SALIDA,
    *,
    salida: Path = DATOS_FINAL,
    lookup_ruta: Path = LOOKUP_MUNICIPIOS,
    manifiesto: Path = CONSOLIDACION_MANIFIESTO,
) -> dict:
    if not entrada.exists():
        raise ConsolidacionError(f"no está {entrada}. Corre primero python -m pipeline.processing.resolver")

    lookup = json.loads(lookup_ruta.read_text(encoding="utf-8"))
    municipios = municipios_desde_lookup(lookup)
    validos = set(municipios)

    with entrada.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        raise ConsolidacionError(f"{entrada} está vacío")

    contratos: dict[str, dict] = {}
    excluidos_por_resolucion = Counter()
    rechazados_modelo = []

    for fila in filas:
        resolucion = (fila.get("municipio_resolucion") or "").strip()
        if resolucion not in RESOLUCIONES_USABLES:
            excluidos_por_resolucion[resolucion or "SIN_RESOLUCION"] += 1
            continue
        ident = (fila.get("id_contrato") or "").strip()
        if ident in contratos:
            excluidos_por_resolucion["ID_DUPLICADO"] += 1
            continue
        try:
            contratos[ident] = fila_a_contrato(fila, validos)
        except (ModeloInvalido, KeyError) as exc:
            rechazados_modelo.append({"id": ident, "motivo": str(exc)})

    datos = validar_conjunto(
        {
            "resumen": {
                "territorio": "Antioquia",
                "fuente": "secop2",
                "nota": (
                    f"{SECOP_FUENTE}. "
                    "Contratos que mencionan varios municipios, que quedaron "
                    "ambiguos o sin resolver no están en este mapa todavía: "
                    "el motivo de cada uno queda en "
                    "data/metadata/consolidacion_manifest.json."
                ),
            },
            "municipios": municipios,
            "contratos": contratos,
            "reportes": {},
            "relaciones": [],
        }
    )

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    resumen = {
        "entrada": str(entrada.relative_to(RAIZ)).replace("\\", "/") if entrada.is_relative_to(RAIZ) else str(entrada),
        "salida": str(salida.relative_to(RAIZ)).replace("\\", "/") if salida.is_relative_to(RAIZ) else str(salida),
        "filas_leidas": len(filas),
        "contratos_incluidos": len(contratos),
        "excluidos_por_resolucion": dict(excluidos_por_resolucion),
        "rechazados_por_modelo": rechazados_modelo,
    }
    manifiesto.parent.mkdir(parents=True, exist_ok=True)
    manifiesto.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK {len(contratos)} contratos -> {salida}")
    print(f"excluidos por resolución: {dict(excluidos_por_resolucion)}")
    if rechazados_modelo:
        print(f"rechazados por el modelo: {len(rechazados_modelo)} (motivo en el manifiesto)")
    return resumen


def main() -> int:
    try:
        consolidar()
        return 0
    except ConsolidacionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
