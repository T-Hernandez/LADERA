"""Búsqueda: pregunta → filtros → datos. La IA no responde de memoria."""

from __future__ import annotations

from datetime import date

from busqueda.ejecutar import ejecutar
from busqueda.ia import interpretar_con_ia
from busqueda.interpretar import interpretar


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
    metodo = reglas["metodo"]
    explicacion = reglas["explicacion"]
    ia_estado = "apagada"
    if usar_ia:
        ia = interpretar_con_ia(pregunta, dane_zona=dane_zona)
        if ia:
            if reglas["filtros"].get("territorio_dane") and not ia.get("territorio_dane"):
                ia["territorio_dane"] = reglas["filtros"]["territorio_dane"]
                ia["territorio"] = ia.get("territorio") or reglas["filtros"].get("territorio")
            filtros = ia
            metodo = "IA"
            explicacion = "Interpretación con IA convertida a filtros. El backend ejecutó la consulta sobre el conjunto analizado."
            ia_estado = "usada"
        else:
            ia_estado = "fallo; se usaron reglas"

    hallado = ejecutar(datos, filtros)
    return {
        "pregunta": pregunta.strip(),
        "interpretacion": {
            "metodo": metodo,
            "ia": ia_estado,
            "explicacion": explicacion,
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
