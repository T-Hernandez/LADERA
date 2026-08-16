"""Búsqueda: pregunta → filtros → datos. La IA no responde de memoria.

Reglas siempre corren primero y son la base. La IA, si está configurada y el
usuario la pidió, solo puede completar campos que las reglas no detectaron —
nunca reemplaza en silencio un filtro que las reglas ya encontraron. En
conflicto explícito, ganan las reglas (ver busqueda.consulta.combinar_filtros).
Sin IA configurada, LADERA funciona igual de bien: nunca depende de ella.
"""

from __future__ import annotations

from datetime import date

from busqueda.consulta import combinar_filtros, filtros_con_contenido, validar_consulta
from busqueda.ejecutar import ejecutar
from busqueda.ia import interpretar_con_ia
from busqueda.interpretar import interpretar
from config import IA_CLAVE, IA_URL


def buscar(
    pregunta: str,
    datos: dict,
    lookup: dict,
    *,
    hoy: date | None = None,
    dane_zona: str | None = None,
    usar_ia: bool = False,
) -> dict:
    hoy = hoy or date.today()
    reglas = interpretar(pregunta, lookup, hoy=hoy, dane_zona=dane_zona)
    filtros = reglas["filtros"]
    metodo = "REGLAS"
    explicacion = reglas["explicacion"]
    ia_configurada = bool(IA_CLAVE and IA_URL)
    ia_estado = "no_configurada"
    conflictos: list[str] = []

    if usar_ia and ia_configurada:
        ia_filtros = interpretar_con_ia(pregunta, dane_zona=dane_zona)
        if ia_filtros:
            filtros, conflictos = combinar_filtros(reglas["filtros"], ia_filtros)
            filtros = validar_consulta(filtros)
            metodo = "REGLAS+IA"
            ia_estado = "usada"
            if filtros_con_contenido(filtros):
                explicacion = (
                    "Reglas y IA se combinaron: la IA solo agrega lo que las reglas no habían "
                    "detectado; si hubo un conflicto, ganó lo que detectaron las reglas. "
                    "El backend ejecutó la consulta sobre el conjunto analizado."
                )
            else:
                explicacion = "No pude identificar filtros suficientes. Puedes precisar municipio, año, estado o tema."
        else:
            ia_estado = "fallo"

    suficiente = filtros_con_contenido(filtros)
    hallado = ejecutar(datos, filtros)
    return {
        "pregunta": pregunta.strip(),
        "interpretacion": {
            "metodo": metodo,
            "ia": ia_estado,
            "explicacion": explicacion,
            "conflictos": conflictos,
            "suficiente": suficiente,
        },
        "filtros": filtros,
        "contratos": hallado["contratos"],
        "reportes": hallado["reportes"],
        "fuentes": hallado["fuentes"],
        "nota": (
            "Cero resultados no significa cero inversión. "
            "Esto no declara irregularidad ni da por verdadero un reporte. "
            "Cada contrato trae su fuente; no se inventa la URL."
        ),
    }
