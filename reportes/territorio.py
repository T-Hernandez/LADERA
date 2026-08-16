"""Punto → municipio. El DANE sale del polígono, no de un nombre escrito."""

from __future__ import annotations


def _en_anillo(lng: float, lat: float, anillo: list) -> bool:
    dentro = False
    n = len(anillo)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = float(anillo[i][0]), float(anillo[i][1])
        xj, yj = float(anillo[j][0]), float(anillo[j][1])
        cruza = (yi > lat) != (yj > lat)
        if cruza:
            x_int = (xj - xi) * (lat - yi) / (yj - yi + 0.0) + xi
            if lng < x_int:
                dentro = not dentro
        j = i
    return dentro


def _en_poligono(lng: float, lat: float, coordenadas: list) -> bool:
    if not coordenadas:
        return False
    if not _en_anillo(lng, lat, coordenadas[0]):
        return False
    for hueco in coordenadas[1:]:
        if _en_anillo(lng, lat, hueco):
            return False
    return True


def _en_geometria(lng: float, lat: float, geom: dict) -> bool:
    tipo = (geom or {}).get("type")
    coords = (geom or {}).get("coordinates") or []
    if tipo == "Polygon":
        return _en_poligono(lng, lat, coords)
    if tipo == "MultiPolygon":
        return any(_en_poligono(lng, lat, pol) for pol in coords)
    return False


def municipio_en_punto(lat: float, lng: float, geojson: dict, prefer_dane: str | None = None) -> dict | None:
    """Devuelve {dane, nombre} del polígono que contiene el punto, o None."""
    hits = []
    for feat in (geojson or {}).get("features") or []:
        props = feat.get("properties") or {}
        if _en_geometria(lng, lat, feat.get("geometry") or {}):
            dane = str(props.get("MPIO_CCNCT") or "").strip()
            nombre = str(props.get("MPIO_CNMBR") or "").strip()
            if dane:
                hits.append({"dane": dane, "nombre": nombre})
    if not hits:
        return None
    if prefer_dane:
        for item in hits:
            if item["dane"] == prefer_dane:
                return item
    return hits[0]
