"""Reglas que convierten una pregunta en filtros. Funciona con la IA apagada."""

from __future__ import annotations

import re
from datetime import date

from busqueda.consulta import consulta_vacia, validar_consulta
from config import MUNICIPIO_ALIAS
from modelo.texto import aparece_como_nombre, norm_busqueda

CATEGORIAS = (
    ("obra inconclusa", "OBRA_INCONCLUSA"),
    ("obras inconclusas", "OBRA_INCONCLUSA"),
    ("inconclusa", "OBRA_INCONCLUSA"),
    ("inconcluso", "OBRA_INCONCLUSA"),
    ("obra deteriorada", "OBRA_DETERIORADA"),
    ("deteriorada", "OBRA_DETERIORADA"),
    ("no visible", "OBRA_NO_VISIBLE"),
    ("problema persistente", "PROBLEMA_PERSISTENTE"),
    ("riesgo", "RIESGO"),
)

STOP_TEXTO = frozenset(
    {
        "muestrame",
        "mostrar",
        "contratos",
        "contrato",
        "reportes",
        "reporte",
        "ciudadanos",
        "que",
        "hay",
        "con",
        "esta",
        "este",
        "zona",
        "aqui",
        "municipio",
        "obras",
        "obra",
        "siguen",
        "teniendo",
        "tienen",
        "terminaron",
        "anio",
        "ano",
        "pasado",
        "relacionados",
        "relacionado",
        "relacionadas",
    }
)


def _indice_municipios(lookup: dict) -> list[tuple[str, str, str]]:
    items = []
    for info in lookup.values():
        nombre = info["nombre"]
        dane = info["dane"]
        items.append((norm_busqueda(nombre), dane, nombre))
    for alias, dane in MUNICIPIO_ALIAS.items():
        oficial = next((i["nombre"] for i in lookup.values() if i["dane"] == dane), alias)
        items.append((norm_busqueda(alias), dane, oficial))
    items.sort(key=lambda t: len(t[0]), reverse=True)
    return items


def interpretar(
    pregunta: str,
    lookup: dict,
    *,
    hoy: date | None = None,
    dane_zona: str | None = None,
) -> dict:
    hoy = hoy or date.today()
    q = norm_busqueda(pregunta)
    crudo = consulta_vacia()
    usados: list[str] = []

    for clave, dane, nombre in _indice_municipios(lookup):
        if clave and aparece_como_nombre(clave, q):
            crudo["territorio_dane"] = dane
            crudo["territorio"] = nombre
            usados.append(clave)
            break

    if "esta zona" in q or "este municipio" in q or "aqui" in q:
        if dane_zona:
            crudo["territorio_dane"] = dane_zona
            usados.append("esta zona")

    if "inconclus" in q:
        crudo["categoria_reporte"] = "OBRA_INCONCLUSA"
        usados.append("inconclus")
    else:
        for frag, cat in CATEGORIAS:
            if frag in q:
                crudo["categoria_reporte"] = cat
                usados.append(frag)
                break

    if any(p in q for p in ("finaliz", "terminaron", "termino")):
        crudo["estado_contrato"] = "FINALIZADO"
        usados.append("finalizado")
    elif any(p in q for p in ("activos", "activo", "en ejecucion", "siguen teniendo", "vigente")):
        crudo["estado_contrato"] = "ACTIVO"
        usados.append("activo")

    if "ano pasado" in q or "anio pasado" in q:
        anio = hoy.year - 1
        crudo["periodo"] = {"desde": f"{anio}-01-01", "hasta": f"{anio}-12-31"}
        usados.append("ano pasado")
    else:
        for anio in range(hoy.year, hoy.year - 8, -1):
            if str(anio) in q:
                crudo["periodo"] = {"desde": f"{anio}-01-01", "hasta": f"{anio}-12-31"}
                usados.append(str(anio))
                break

    if any(
        p in q
        for p in (
            "tienen reportes",
            "con reportes",
            "reportes de",
            "reportes ciudadanos",
            "teniendo reportes",
        )
    ):
        crudo["con_reportes"] = True
        usados.append("con reportes")

    if "relacionad" in q:
        crudo["con_relacion"] = True
        usados.append("relacionados")

    resto = []
    for tok in re.findall(r"[a-z0-9]+", q):
        if tok in STOP_TEXTO or len(tok) < 4:
            continue
        if any(tok in u or u in tok for u in usados if u):
            continue
        resto.append(tok)
    if resto:
        crudo["texto"] = " ".join(resto)

    filtros = validar_consulta(crudo)
    partes = []
    if filtros["territorio"] or filtros["territorio_dane"]:
        partes.append(f"territorio {filtros['territorio'] or filtros['territorio_dane']}")
    if filtros["estado_contrato"]:
        partes.append(f"estado {filtros['estado_contrato']}")
    if filtros["categoria_reporte"]:
        partes.append(f"categoría {filtros['categoria_reporte']}")
    if filtros["periodo"]:
        partes.append(
            f"periodo {filtros['periodo'].get('desde') or ''} a {filtros['periodo'].get('hasta') or ''}"
        )
    if filtros["con_reportes"]:
        partes.append("solo contratos con reportes")
    if filtros["con_relacion"]:
        partes.append("con relación registrada")
    if filtros["texto"]:
        partes.append(f"texto «{filtros['texto']}»")
    explicacion = (
        "Se interpretó así: " + "; ".join(partes) + "."
        if partes
        else "No se reconocieron filtros; se busca el texto en el conjunto analizado."
    )
    if not partes and pregunta.strip():
        filtros["texto"] = norm_busqueda(pregunta)
        explicacion = f"Búsqueda por texto en el conjunto analizado: «{filtros['texto']}»."
    return {"filtros": filtros, "metodo": "REGLAS", "explicacion": explicacion}
