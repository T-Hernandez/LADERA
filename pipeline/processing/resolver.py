"""Fase 5: resolver territorio y tiempo sobre el limpio. No vuelve a descargar."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    CIUDADES_VACIAS,
    CURACION_LIMPIO,
    DIR_FINAL,
    DIR_INTERIM,
    LOOKUP_MUNICIPIOS,
    MUNICIPIO_ALIAS,
    MUNICIPIO_AMBIGUO,
    RESOLUCION_MANIFIESTO,
    RESOLUCION_REPORTE,
    RESOLUCION_SALIDA,
)
from modelo.constantes import MUNICIPIOS_ESPERADOS  # noqa: E402
from modelo.texto import fragmento_en_texto, norm_busqueda  # noqa: E402
from pipeline.processing.curar import parse_fecha  # noqa: E402

CAMPOS_EXTRA = (
    "municipio_dane",
    "municipio_nombre",
    "municipio_resolucion",
    "municipios_mencionados",
    "ubicacion_submunicipal",
    "ubicacion_fragmento",
    "ubicacion_fuente",
    "anio_firma",
    "duracion_dias",
)

RESOLUCIONES = (
    "OBJETO",
    "CIUDAD_ENTIDAD",
    "MULTIMUNICIPIO",
    "AMBIGUO",
    "SIN_RESOLVER",
)

CIUDADES_VACIAS_NORM = tuple(norm_busqueda(c) for c in CIUDADES_VACIAS)

# Más específico primero. El nombre se corta en coma, punto o conector.
_PATRONES_LUGAR = (
    (re.compile(r"(vereda|vda\.?)\s+(?:de\s+)?([^.,;:\n]{3,60})", re.I), "vereda"),
    (re.compile(r"(corregimiento|corr\.?)\s+(?:de\s+)?([^.,;:\n]{3,60})", re.I), "corregimiento"),
    (re.compile(r"(barrio)\s+([^.,;:\n]{3,60})", re.I), "barrio"),
    (re.compile(r"(sector)\s+(?:de\s+)?([^.,;:\n]{3,60})", re.I), "sector"),
    (re.compile(r"(comuna)\s+(\d+|[^.,;:\n]{3,60})", re.I), "comuna"),
    (re.compile(r"(v[ií]a)\s+([^.,;:\n]{3,60})", re.I), "via"),
)

_CORTE_LUGAR = re.compile(
    r"\s+(?:en|para|con|mediante|ubicad[oa]s?|del municipio|del departamento|"
    r"del contrato|de antioquia|desde|hasta|"
    r"y\s+(?:la\s+|el\s+)?(?:remodelaci|construcci|mantenim|adecuaci|"
    r"terminaci|ejecuci|optimizaci))\b",
    re.I,
)

_GENERICOS_LUGAR = {
    "terciaria",
    "secundaria",
    "principal",
    "urbana",
    "rural",
    "veredal",
    "nacional",
    "departamental",
    "de acceso",
    "arterial",
    "educativo",
    "salud",
    "publico",
    "privado",
    "solidario",
    "transporte",
    "comercio",
    "industrial",
    "agropecuario",
    "turistico",
}


class ResolucionError(RuntimeError):
    pass


class IndiceTerritorial:
    def __init__(self, por_dane: dict[str, str], por_clave: dict[str, tuple[str, ...]]):
        self.por_dane = por_dane
        self.por_clave = por_clave
        self.terminos = sorted(por_clave.items(), key=lambda item: len(item[0]), reverse=True)
        self.nombres_norm = {norm_busqueda(nombre) for nombre in por_dane.values()}

    def es_solo_municipio(self, texto: str) -> bool:
        return norm_busqueda(texto) in self.nombres_norm or norm_busqueda(texto) in self.por_clave


def _hash_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def cargar_indice(ruta: Path = LOOKUP_MUNICIPIOS) -> IndiceTerritorial:
    data = json.loads(ruta.read_text(encoding="utf-8"))
    if len(data) != MUNICIPIOS_ESPERADOS:
        raise ResolucionError(f"se esperaban {MUNICIPIOS_ESPERADOS} municipios, hay {len(data)}")

    por_dane: dict[str, str] = {}
    por_clave: dict[str, tuple[str, ...]] = {}

    for info in data.values():
        dane = str(info["dane"]).strip()
        nombre = str(info["nombre"]).strip()
        if dane in por_dane and por_dane[dane] != nombre:
            raise ResolucionError(f"DANE repetido con otro nombre: {dane}")
        por_dane[dane] = nombre
        clave = norm_busqueda(nombre)
        if clave in por_clave and por_clave[clave] != (dane,):
            raise ResolucionError(f"nombre de municipio colisiona: {nombre}")
        por_clave[clave] = (dane,)

    if len(por_dane) != MUNICIPIOS_ESPERADOS:
        raise ResolucionError(f"DANE unicos: {len(por_dane)}, se esperaban {MUNICIPIOS_ESPERADOS}")

    for alias, dane in MUNICIPIO_ALIAS.items():
        clave = norm_busqueda(alias)
        if dane not in por_dane:
            raise ResolucionError(f"alias {alias} apunta a DANE desconocido {dane}")
        if clave in por_clave and por_clave[clave] != (dane,):
            raise ResolucionError(f"alias {alias} choca con otro municipio")
        por_clave[clave] = (dane,)

    for alias, danes in MUNICIPIO_AMBIGUO.items():
        clave = norm_busqueda(alias)
        if clave in por_clave and len(por_clave[clave]) == 1:
            raise ResolucionError(f"ambiguo {alias} pisa un nombre oficial")
        for dane in danes:
            if dane not in por_dane:
                raise ResolucionError(f"ambiguo {alias} apunta a DANE desconocido {dane}")
        por_clave[clave] = tuple(danes)

    return IndiceTerritorial(por_dane, por_clave)


def _spans_contenidos(inicio: int, fin: int, aceptados: list[tuple[int, int]]) -> bool:
    return any(inicio >= a and fin <= b for a, b in aceptados)


def mencionar_municipios(texto: str, indice: IndiceTerritorial) -> tuple[list[str], list[str]]:
    """Devuelve (danes unicos, danes de menciones ambiguas no cubiertas)."""
    cuerpo = norm_busqueda(texto)
    if not cuerpo:
        return [], []

    unicos: list[str] = []
    ambiguos: list[str] = []
    spans: list[tuple[int, int]] = []

    for clave, danes in indice.terminos:
        patron = re.compile(r"(?<!\w)" + re.escape(clave) + r"(?!\w)")
        for match in patron.finditer(cuerpo):
            if _spans_contenidos(match.start(), match.end(), spans):
                continue
            spans.append((match.start(), match.end()))
            if len(danes) == 1:
                if danes[0] not in unicos:
                    unicos.append(danes[0])
            else:
                for dane in danes:
                    if dane not in ambiguos:
                        ambiguos.append(dane)
    return unicos, ambiguos


def resolver_ciudad(ciudad: str, indice: IndiceTerritorial) -> tuple[list[str], str]:
    clave = norm_busqueda(ciudad)
    if not clave or clave in CIUDADES_VACIAS_NORM:
        return [], "vacio"
    danes = indice.por_clave.get(clave)
    if not danes:
        return [], "desconocido"
    if len(danes) > 1:
        return list(danes), "ambiguo"
    return [danes[0]], "unico"


def _cortar_lugar(crudo: str) -> str:
    corte = _CORTE_LUGAR.search(crudo)
    texto = crudo[: corte.start()] if corte else crudo
    return texto.strip(" .,-")


def extraer_submunicipal(texto: str, indice: IndiceTerritorial) -> tuple[str, str, str]:
    """(etiqueta, fragmento literal, fuente). Vacio si no hay fragmento verificable."""
    original = texto or ""
    if not original.strip():
        return "", "", ""

    for patron, tipo in _PATRONES_LUGAR:
        match = patron.search(original)
        if not match:
            continue
        matched = original[match.start() : match.end()]
        fragmento = _cortar_lugar(matched)
        if len(norm_busqueda(fragmento)) < 6:
            continue
        nombre = _cortar_lugar(match.group(2))
        if not nombre or indice.es_solo_municipio(nombre):
            continue
        if norm_busqueda(nombre) in _GENERICOS_LUGAR:
            continue
        if not fragmento_en_texto(fragmento, original):
            continue
        return f"{tipo} {nombre}".strip(), fragmento, "objeto_del_contrato"
    return "", "", ""


def aceptar_ubicacion(fragmento: str, texto: str) -> bool:
    return fragmento_en_texto(fragmento, texto)


def _anio(fecha_norm: str) -> str:
    return fecha_norm[:4] if fecha_norm and len(fecha_norm) >= 4 else ""


def _duracion_dias(inicio: str, fin: str) -> str:
    a = parse_fecha(inicio)
    b = parse_fecha(fin)
    if a is None or b is None:
        return ""
    dias = (b - a).days
    return str(dias) if dias >= 0 else ""


def resolver_fila(fila: dict, indice: IndiceTerritorial) -> dict:
    objeto = fila.get("objeto_del_contrato") or ""
    ciudad = fila.get("ciudad") or ""
    unicos, ambiguos = mencionar_municipios(objeto, indice)

    if len(unicos) == 1:
        resolucion = "OBJETO"
        danes = unicos
    elif len(unicos) >= 2:
        resolucion = "MULTIMUNICIPIO"
        danes = unicos
    elif ambiguos:
        resolucion = "AMBIGUO"
        danes = ambiguos
    else:
        ciudad_danes, tipo = resolver_ciudad(ciudad, indice)
        if tipo == "unico":
            resolucion = "CIUDAD_ENTIDAD"
            danes = ciudad_danes
        elif tipo == "ambiguo":
            resolucion = "AMBIGUO"
            danes = ciudad_danes
        else:
            resolucion = "SIN_RESOLVER"
            danes = []

    dane_principal = danes[0] if resolucion in {"OBJETO", "CIUDAD_ENTIDAD"} and danes else ""
    nombre = indice.por_dane.get(dane_principal, "")
    lugar, fragmento, fuente = extraer_submunicipal(objeto, indice)
    inicio = fila.get("fecha_inicio_norm") or fila.get("fecha_de_inicio_del_contrato") or ""
    fin = fila.get("fecha_fin_norm") or fila.get("fecha_de_fin_del_contrato") or ""
    firma = fila.get("fecha_firma_norm") or fila.get("fecha_de_firma") or ""

    salida = dict(fila)
    salida.update(
        {
            "municipio_dane": dane_principal,
            "municipio_nombre": nombre,
            "municipio_resolucion": resolucion,
            "municipios_mencionados": ";".join(danes),
            "ubicacion_submunicipal": lugar,
            "ubicacion_fragmento": fragmento,
            "ubicacion_fuente": fuente,
            "anio_firma": _anio(firma),
            "duracion_dias": _duracion_dias(inicio, fin),
        }
    )
    return salida


def activo_en_periodo(fila: dict, desde: date, hasta: date) -> bool:
    """La vigencia se solapa con [desde, hasta]. Sin fechas, se usa la firma."""
    if desde > hasta:
        raise ResolucionError("el periodo tiene desde > hasta")
    ini = parse_fecha(fila.get("fecha_inicio_norm") or fila.get("fecha_de_inicio_del_contrato"))
    fin = parse_fecha(fila.get("fecha_fin_norm") or fila.get("fecha_de_fin_del_contrato"))
    if ini is None and fin is None:
        firma = parse_fecha(fila.get("fecha_firma_norm") or fila.get("fecha_de_firma"))
        return firma is not None and desde <= firma <= hasta
    if ini is None:
        ini = fin
    if fin is None:
        fin = ini
    assert ini is not None and fin is not None
    return ini <= hasta and fin >= desde


def _danes_de_fila(fila: dict) -> set[str]:
    danes = set()
    if fila.get("municipio_dane"):
        danes.add(fila["municipio_dane"])
    for parte in (fila.get("municipios_mencionados") or "").split(";"):
        if parte:
            danes.add(parte)
    return danes


def _estado_filtro(fila: dict) -> str:
    return (fila.get("estado_normalizado") or fila.get("estado") or "").strip()


def filtrar_contratos(
    filas: list[dict],
    *,
    dane: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    estado: str | None = None,
    anio: int | str | None = None,
) -> list[dict]:
    """Responde: que contratos estuvieron activos en este territorio en este periodo."""
    pedido = (estado or "").strip().casefold()
    if pedido == "expirado":
        pedido = "finalizado"
    anio_txt = str(anio) if anio is not None else None
    salida = []
    for fila in filas:
        if dane and dane not in _danes_de_fila(fila):
            continue
        if anio_txt and fila.get("anio_firma") != anio_txt:
            continue
        if pedido:
            actual = _estado_filtro(fila).casefold()
            if pedido == "activo" and actual not in {"activo", "proximo_a_vencer"}:
                continue
            if pedido == "finalizado" and actual != "finalizado":
                continue
            if pedido not in {"activo", "finalizado"} and actual != pedido:
                continue
        if desde and hasta and not activo_en_periodo(fila, desde, hasta):
            continue
        salida.append(fila)
    return salida


def resolver(
    entrada: Path | None = None,
    *,
    salida: Path = RESOLUCION_SALIDA,
    reporte: Path = RESOLUCION_REPORTE,
    manifiesto: Path = RESOLUCION_MANIFIESTO,
    lookup: Path = LOOKUP_MUNICIPIOS,
) -> dict:
    origen = Path(entrada) if entrada else CURACION_LIMPIO
    if not origen.exists():
        raise ResolucionError(f"no esta {origen}. Corre primero python -m pipeline.processing")

    indice = cargar_indice(lookup)
    with origen.open(encoding="utf-8", newline="") as fh:
        lector = csv.DictReader(fh)
        if not lector.fieldnames:
            raise ResolucionError(f"{origen} no tiene encabezado")
        originales = list(lector.fieldnames)
        filas = list(lector)
    if not filas:
        raise ResolucionError(f"{origen} esta vacio")

    resueltas = [resolver_fila(fila, indice) for fila in filas]
    DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    DIR_FINAL.mkdir(parents=True, exist_ok=True)
    campos = list(originales)
    for extra in CAMPOS_EXTRA:
        if extra not in campos:
            campos.append(extra)
    with salida.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(resueltas)

    por_res = Counter(f["municipio_resolucion"] for f in resueltas)
    ciudades_sin = Counter(
        (f.get("ciudad") or "").strip() or "(vacio)"
        for f in resueltas
        if f["municipio_resolucion"] == "SIN_RESOLVER"
    )
    sub = sum(1 for f in resueltas if f["ubicacion_submunicipal"])
    anios = Counter(f["anio_firma"] or "(sin anio)" for f in resueltas)
    resumen = {
        "entrada": str(origen.relative_to(RAIZ)).replace("\\", "/") if origen.is_relative_to(RAIZ) else str(origen),
        "hash_entrada": _hash_archivo(origen),
        "filas": len(resueltas),
        "municipios_lookup": len(indice.por_dane),
        "resolucion": {k: por_res.get(k, 0) for k in RESOLUCIONES},
        "con_submunicipal": sub,
        "anios_firma": dict(anios),
        "ciudades_sin_resolver": dict(ciudades_sin.most_common(15)),
    }
    texto = [
        "LADERA — reporte de resolucion territorial (Fase 5)",
        f"entrada: {resumen['entrada']}",
        f"hash: {resumen['hash_entrada']}",
        f"filas: {resumen['filas']}",
        f"municipios en lookup: {resumen['municipios_lookup']}",
        f"OBJETO: {por_res.get('OBJETO', 0)}",
        f"CIUDAD_ENTIDAD: {por_res.get('CIUDAD_ENTIDAD', 0)}",
        f"MULTIMUNICIPIO: {por_res.get('MULTIMUNICIPIO', 0)}",
        f"AMBIGUO: {por_res.get('AMBIGUO', 0)}",
        f"SIN_RESOLVER: {por_res.get('SIN_RESOLVER', 0)}",
        f"con lugar submunicipal: {sub}",
        f"anios de firma: {dict(anios)}",
        f"ciudades sin resolver: {resumen['ciudades_sin_resolver']}",
        "",
        "Un MULTIMUNICIPIO registra todos los DANE. El valor no se parte.",
        "AMBIGUO no se resuelve con IA en esta fase.",
        "Sin fragmento literal no hay vereda, barrio ni sector.",
    ]
    reporte.write_text("\n".join(texto) + "\n", encoding="utf-8")
    manifiesto.parent.mkdir(parents=True, exist_ok=True)
    manifiesto.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(texto[:12]))
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resuelve municipio y periodo sobre el limpio.")
    parser.add_argument("--entrada", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        resolver(args.entrada)
        return 0
    except ResolucionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
