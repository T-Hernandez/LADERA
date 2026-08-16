"""Constructores. Si un campo no cumple el contrato, no se crea el objeto."""

from __future__ import annotations

from datetime import date

from modelo.constantes import (
    CATEGORIAS_REPORTE,
    ESTADOS_CONTRATO,
    ESTADOS_RELACION,
    ESTADOS_REPORTE,
    FUENTES,
    METODOS_RELACION,
    SENALES_RELACION,
    TIPOS_EVIDENCIA,
    TIPOS_EXTREMO,
    TIPOS_RELACION,
)
from modelo.errores import ModeloInvalido
from modelo.texto import fragmento_en_texto


def _texto(valor, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ModeloInvalido(f"{campo} no puede estar vacío")
    return valor.strip()


def _opcional(valor):
    if valor is None:
        return None
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


def _fecha_dia(valor, campo: str) -> str:
    texto = _texto(valor, campo)
    try:
        date.fromisoformat(texto)
    except ValueError as exc:
        raise ModeloInvalido(f"{campo} debe ser YYYY-MM-DD") from exc
    return texto


def _coord(valor, campo: str):
    if valor is None or valor == "":
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ModeloInvalido(f"{campo} no es numérico") from exc
    return numero


def municipio_vacio(nombre: str, dane: str) -> dict:
    dane = _texto(dane, "dane")
    if len(dane) != 5 or not dane.isdigit():
        raise ModeloInvalido(f"dane inválido: {dane}")
    return {
        "nombre": _texto(nombre, "nombre"),
        "dane": dane,
        "contratos": 0,
        "reportes": 0,
        "plata_total": 0,
        "contrato_ids": [],
        "reporte_ids": [],
    }


def ubicacion_contrato(nombre: str, fragmento: str, fuente: str, texto_original: str) -> dict:
    frag = _texto(fragmento, "fragmento")
    if not fragmento_en_texto(frag, texto_original):
        raise ModeloInvalido(
            "la ubicación submunicipal no entra: el fragmento no está en el texto original"
        )
    return {
        "nombre": _texto(nombre, "nombre de ubicación"),
        "fragmento": frag,
        "fuente": _texto(fuente, "fuente de ubicación"),
    }


def contrato(
    *,
    id: str,
    fuente: str,
    url_fuente: str | None,
    objeto: str,
    entidad: str,
    contratista: str | None,
    valor,
    valor_motivo: str | None,
    fecha_firma: str | None,
    fecha_inicio: str | None,
    fecha_fin: str | None,
    estado: str,
    municipio_dane: str,
    municipio_nombre: str,
    ubicaciones: list[dict],
    texto_original: str,
    municipios_validos: set[str] | None = None,
) -> dict:
    ident = _texto(id, "id")
    if fuente not in FUENTES:
        raise ModeloInvalido(f"fuente no permitida: {fuente}")
    if estado not in ESTADOS_CONTRATO:
        raise ModeloInvalido(f"estado de contrato no permitido: {estado}")
    dane = _texto(municipio_dane, "municipio_dane")
    if municipios_validos is not None and dane not in municipios_validos:
        raise ModeloInvalido(f"municipio inexistente: {dane}")
    if url_fuente is not None and not str(url_fuente).startswith("http"):
        raise ModeloInvalido("url_fuente debe leerse del dataset, no inventarse")
    if valor is None:
        if not valor_motivo:
            raise ModeloInvalido("un valor nulo necesita valor_motivo")
    else:
        if not isinstance(valor, (int, float)) or valor < 0:
            raise ModeloInvalido("valor debe ser un número >= 0 o null")
        if valor_motivo:
            raise ModeloInvalido("valor utilizable no lleva valor_motivo")

    texto = _texto(texto_original, "texto_original")
    lugares = [
        ubicacion_contrato(
            u["nombre"], u["fragmento"], u["fuente"], texto
        )
        for u in (ubicaciones or [])
    ]
    return {
        "id": ident,
        "fuente": fuente,
        "url_fuente": url_fuente,
        "objeto": _texto(objeto, "objeto"),
        "entidad": _texto(entidad, "entidad"),
        "contratista": _opcional(contratista),
        "valor": valor,
        "valor_motivo": _opcional(valor_motivo),
        "fecha_firma": _opcional(fecha_firma),
        "fecha_inicio": _opcional(fecha_inicio),
        "fecha_fin": _opcional(fecha_fin),
        "estado": estado,
        "municipio_dane": dane,
        "municipio_nombre": _texto(municipio_nombre, "municipio_nombre"),
        "ubicaciones": lugares,
        "texto_original": texto,
    }


def evidencia(
    *,
    id: str,
    tipo: str,
    url: str,
    fecha: str,
    metadata: dict | None = None,
) -> dict:
    if tipo not in TIPOS_EVIDENCIA:
        raise ModeloInvalido(f"tipo de evidencia no permitido: {tipo}")
    return {
        "id": _texto(id, "id de evidencia"),
        "tipo": tipo,
        "url": _texto(url, "url de evidencia"),
        "fecha": _texto(fecha, "fecha de evidencia"),
        "metadata": metadata or {},
    }


def reporte(
    *,
    id: str,
    fecha_creacion: str,
    fecha_observacion: str,
    descripcion: str,
    categoria: str,
    estado: str,
    autor: str,
    ubicacion: dict,
    evidencias: list[dict] | None = None,
    municipios_validos: set[str] | None = None,
) -> dict:
    if categoria not in CATEGORIAS_REPORTE:
        raise ModeloInvalido(f"categoría no permitida: {categoria}")
    if estado not in ESTADOS_REPORTE:
        raise ModeloInvalido(f"estado de reporte no permitido: {estado}")
    dane = _texto(ubicacion.get("dane"), "ubicacion.dane")
    if municipios_validos is not None and dane not in municipios_validos:
        raise ModeloInvalido(f"municipio inexistente: {dane}")
    evs = [
        evidencia(
            id=e["id"],
            tipo=e["tipo"],
            url=e["url"],
            fecha=e["fecha"],
            metadata=e.get("metadata"),
        )
        for e in (evidencias or [])
    ]
    lat = _coord(ubicacion.get("lat"), "ubicacion.lat")
    lng = _coord(ubicacion.get("lng"), "ubicacion.lng")
    if (lat is None) != (lng is None):
        raise ModeloInvalido("lat y lng van juntos")
    if lat is not None and not (-90 <= lat <= 90):
        raise ModeloInvalido("lat fuera de rango")
    if lng is not None and not (-180 <= lng <= 180):
        raise ModeloInvalido("lng fuera de rango")
    return {
        "id": _texto(id, "id"),
        "fecha_creacion": _texto(fecha_creacion, "fecha_creacion"),
        "fecha_observacion": _fecha_dia(fecha_observacion, "fecha_observacion"),
        "descripcion": _texto(descripcion, "descripcion"),
        "categoria": categoria,
        "estado": estado,
        "autor": _texto(autor, "autor"),
        "ubicacion": {
            "dane": dane,
            "nombre": _texto(ubicacion.get("nombre"), "ubicacion.nombre"),
            "detalle": _opcional(ubicacion.get("detalle")),
            "lat": lat,
            "lng": lng,
        },
        "evidencias": evs,
    }


def relacion(
    *,
    id: str,
    origen: dict,
    destino: dict,
    tipo_relacion: str,
    metodo: str,
    estado: str,
    evidencia: str,
    creado_en: str,
    confianza=None,
    revisado_en: str | None = None,
    senales: list[str] | None = None,
    motivo_revision: str | None = None,
    ids_contrato: set[str] | None = None,
    ids_reporte: set[str] | None = None,
) -> dict:
    if tipo_relacion not in TIPOS_RELACION:
        raise ModeloInvalido(f"tipo_relacion no permitido: {tipo_relacion}")
    if metodo not in METODOS_RELACION:
        raise ModeloInvalido(f"metodo no permitido: {metodo}")
    if estado not in ESTADOS_RELACION:
        raise ModeloInvalido(f"estado de relación no permitido: {estado}")
    if metodo == "IA" and estado == "CONFIRMADA":
        raise ModeloInvalido("la IA no puede crear una relación CONFIRMADA")
    ev = _texto(evidencia, "evidencia de la relación")
    for s in senales or []:
        if s not in SENALES_RELACION:
            raise ModeloInvalido(f"señal no permitida: {s}")

    def extremo(pieza: dict, campo: str) -> dict:
        tipo = pieza.get("tipo")
        ident = _texto(pieza.get("id"), f"{campo}.id")
        if tipo not in TIPOS_EXTREMO:
            raise ModeloInvalido(f"{campo}.tipo no permitido: {tipo}")
        if ids_contrato is not None and tipo == "contrato" and ident not in ids_contrato:
            raise ModeloInvalido(f"contrato inexistente en la relación: {ident}")
        if ids_reporte is not None and tipo == "reporte" and ident not in ids_reporte:
            raise ModeloInvalido(f"reporte inexistente en la relación: {ident}")
        return {"tipo": tipo, "id": ident}

    o = extremo(origen, "origen")
    d = extremo(destino, "destino")
    tipos = {o["tipo"], d["tipo"]}
    if tipos != {"contrato", "reporte"}:
        raise ModeloInvalido("una relación vincula un reporte con un contrato")
    if confianza is not None and not (0 <= float(confianza) <= 1):
        raise ModeloInvalido("confianza, si existe, va entre 0 y 1")
    return {
        "id": _texto(id, "id"),
        "origen": o,
        "destino": d,
        "tipo_relacion": tipo_relacion,
        "metodo": metodo,
        "confianza": confianza,
        "estado": estado,
        "evidencia": ev,
        "creado_en": _texto(creado_en, "creado_en"),
        "revisado_en": _opcional(revisado_en),
        "senales": sorted(set(senales or [])),
        "motivo_revision": _opcional(motivo_revision),
    }
