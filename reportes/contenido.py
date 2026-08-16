"""Rechaza texto que no es una observación. No es un filtro político."""

from __future__ import annotations

import re

from modelo.texto import norm_busqueda

_URL = re.compile(r"https?://\S+", re.I)
_SOLO_RUIDO = re.compile(r"^(asdf|qwer|test|prueba|xxx|lorem|ipsum|abc|hola){1,8}$")


def rechazo_contenido(descripcion: str, minimo: int = 20) -> str | None:
    texto = " ".join(str(descripcion or "").split())
    if len(texto) < minimo:
        return f"describe lo que observaste (mínimo {minimo} caracteres)"
    letras = re.findall(r"[a-záéíóúñü]", texto.casefold())
    if len(letras) < 12:
        return "el texto no describe una observación"
    sin_url = _URL.sub(" ", texto).strip()
    if len(sin_url) < 12:
        return "un enlace solo no es una observación"
    compacto = re.sub(r"[^a-z0-9]+", "", norm_busqueda(texto))
    if compacto and len(set(compacto)) <= 2 and len(compacto) >= 8:
        return "el texto no describe una observación"
    if _SOLO_RUIDO.fullmatch(compacto):
        return "el texto no describe una observación"
    return None
