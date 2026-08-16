"""El conjunto canónico: 125 municipios + entidades + agregados deterministas."""

from __future__ import annotations

from modelo.constantes import ESTADOS_REPORTE_VISIBLES, MUNICIPIOS_ESPERADOS
from modelo.entidades import contrato, municipio_vacio, relacion, reporte
from modelo.errores import ModeloInvalido


def municipios_desde_lookup(lookup: dict) -> dict[str, dict]:
    municipios = {
        item["dane"]: municipio_vacio(item["nombre"], item["dane"])
        for item in lookup.values()
    }
    if len(municipios) != MUNICIPIOS_ESPERADOS:
        raise ModeloInvalido(
            f"se esperaban {MUNICIPIOS_ESPERADOS} municipios, hay {len(municipios)}"
        )
    return municipios


def recomputar(datos: dict) -> dict:
    """Los agregados salen de las entidades. El frontend no los recalcula."""
    municipios = datos["municipios"]
    for mun in municipios.values():
        mun["contrato_ids"] = []
        mun["reporte_ids"] = []
        mun["contratos"] = 0
        mun["reportes"] = 0
        mun["plata_total"] = 0

    for c in datos["contratos"].values():
        mun = municipios[c["municipio_dane"]]
        mun["contrato_ids"].append(c["id"])
    for r in datos["reportes"].values():
        if r.get("estado") not in ESTADOS_REPORTE_VISIBLES:
            continue
        mun = municipios[r["ubicacion"]["dane"]]
        mun["reporte_ids"].append(r["id"])

    for mun in municipios.values():
        mun["contratos"] = len(mun["contrato_ids"])
        mun["reportes"] = len(mun["reporte_ids"])
        mun["plata_total"] = sum(
            datos["contratos"][cid]["valor"] or 0 for cid in mun["contrato_ids"]
        )

    contratos = datos["contratos"]
    resumen = datos.setdefault("resumen", {})
    resumen["municipios"] = len(municipios)
    resumen["contratos"] = len(contratos)
    resumen["contratos_con_cifra"] = sum(
        1 for c in contratos.values() if c["valor"] is not None
    )
    resumen["plata_total"] = sum(c["valor"] or 0 for c in contratos.values())
    resumen["reportes"] = sum(
        1 for r in datos["reportes"].values() if r.get("estado") in ESTADOS_REPORTE_VISIBLES
    )
    resumen["relaciones"] = len(datos["relaciones"])
    resumen["municipios_con_contratos"] = sum(
        1 for m in municipios.values() if m["contratos"] > 0
    )
    resumen["municipios_sin_contratos"] = sum(
        1 for m in municipios.values() if m["contratos"] == 0
    )
    resumen["municipios_con_reportes"] = sum(
        1 for m in municipios.values() if m["reportes"] > 0
    )
    return datos


def validar_conjunto(datos: dict, municipios_esperados: int = MUNICIPIOS_ESPERADOS) -> dict:
    municipios = datos.get("municipios") or {}
    if len(municipios) != municipios_esperados:
        raise ModeloInvalido(
            f"deben existir {municipios_esperados} municipios, hay {len(municipios)}"
        )
    validos = set(municipios)
    for dane, mun in municipios.items():
        if mun.get("dane") != dane:
            raise ModeloInvalido(f"la clave {dane} no coincide con dane={mun.get('dane')}")

    contratos = {}
    for ident, crudo in (datos.get("contratos") or {}).items():
        c = contrato(**{k: crudo[k] for k in _CAMPOS_CONTRATO}, municipios_validos=validos)
        if c["id"] != ident:
            raise ModeloInvalido(f"la clave {ident} no coincide con id={c['id']}")
        contratos[ident] = c

    reportes = {}
    for ident, crudo in (datos.get("reportes") or {}).items():
        r = reporte(
            id=crudo["id"],
            fecha_creacion=crudo["fecha_creacion"],
            fecha_observacion=crudo["fecha_observacion"],
            descripcion=crudo["descripcion"],
            categoria=crudo["categoria"],
            estado=crudo["estado"],
            autor=crudo["autor"],
            ubicacion=crudo["ubicacion"],
            evidencias=crudo.get("evidencias"),
            municipios_validos=validos,
        )
        if r["id"] != ident:
            raise ModeloInvalido(f"la clave {ident} no coincide con id={r['id']}")
        reportes[ident] = r

    ids_c = set(contratos)
    ids_r = set(reportes)
    relaciones = [
        relacion(
            id=rel["id"],
            origen=rel["origen"],
            destino=rel["destino"],
            tipo_relacion=rel["tipo_relacion"],
            metodo=rel["metodo"],
            estado=rel["estado"],
            evidencia=rel["evidencia"],
            creado_en=rel["creado_en"],
            confianza=rel.get("confianza"),
            revisado_en=rel.get("revisado_en"),
            senales=rel.get("senales"),
            motivo_revision=rel.get("motivo_revision"),
            ids_contrato=ids_c,
            ids_reporte=ids_r,
        )
        for rel in (datos.get("relaciones") or [])
    ]

    limpio = {
        "resumen": dict(datos.get("resumen") or {}),
        "municipios": {k: dict(v) for k, v in municipios.items()},
        "contratos": contratos,
        "reportes": reportes,
        "relaciones": relaciones,
    }
    recomputar(limpio)

    r = limpio["resumen"]
    if r["contratos_con_cifra"] > r["contratos"]:
        raise ModeloInvalido("contratos_con_cifra no puede superar a contratos")
    if r["municipios_con_contratos"] + r["municipios_sin_contratos"] != r["municipios"]:
        raise ModeloInvalido("la cobertura municipal no cierra")
    return limpio


_CAMPOS_CONTRATO = (
    "id",
    "fuente",
    "url_fuente",
    "objeto",
    "entidad",
    "contratista",
    "valor",
    "valor_motivo",
    "fecha_firma",
    "fecha_inicio",
    "fecha_fin",
    "estado",
    "municipio_dane",
    "municipio_nombre",
    "ubicaciones",
    "texto_original",
)
