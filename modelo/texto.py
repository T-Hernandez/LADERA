import re
import unicodedata


def norm(texto: str) -> str:
    """Normaliza para comparar un fragmento contra el texto original."""
    return " ".join(str(texto).casefold().split())


def norm_busqueda(texto: str) -> str:
    """Quita tildes y colapsa espacios. Sirve para cruzar ciudad, objeto y lookup."""
    descompuesto = unicodedata.normalize("NFD", str(texto or ""))
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.casefold().split())


def aparece_como_nombre(nombre: str, texto: str) -> bool:
    """El nombre entra como frase, no como subcadena (bello no pega en bellota)."""
    clave = norm_busqueda(nombre)
    cuerpo = norm_busqueda(texto)
    if not clave or not cuerpo:
        return False
    return re.search(r"(?<!\w)" + re.escape(clave) + r"(?!\w)", cuerpo) is not None


def fragmento_en_texto(fragmento: str, texto: str) -> bool:
    frag = norm(fragmento)
    return bool(frag) and frag in norm(texto)
