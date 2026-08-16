def norm(texto: str) -> str:
    """Normaliza para comparar un fragmento contra el texto original."""
    return " ".join(str(texto).casefold().split())


def fragmento_en_texto(fragmento: str, texto: str) -> bool:
    frag = norm(fragmento)
    return bool(frag) and frag in norm(texto)
