"""IA opcional para posibles conexiones: solo explica, nunca decide.

La IA no puede sugerir una conexión que las reglas no hayan detectado antes
(relaciones/motor.py sigue siendo el único que decide si un par se sugiere),
y no puede cambiar su estado ni su confianza. Lo único que hace es traducir
las señales que las reglas ya encontraron a un párrafo en lenguaje llano.
"""

from __future__ import annotations

from ia_cliente import llamar_ia

SISTEMA = (
    "Explicas en un párrafo corto y en español sencillo, a un ciudadano sin "
    "formación técnica, por qué un sistema de reglas propuso contrastar un "
    "reporte ciudadano con un contrato público. Usas SOLO los datos que se "
    "te dan — nunca afirmas que el contrato causó el problema ni que el "
    "reporte es cierto, solo explicas por qué vale la pena revisarlos juntos. "
    "Máximo 3 frases. Sin JSON, sin markdown: solo el párrafo."
)


def explicar_relacion(*, reporte: dict, contrato: dict, senales: list[str], evidencia_reglas: str) -> str | None:
    contexto = (
        f"Reporte ciudadano: categoría {reporte.get('categoria')}, "
        f"descripción: \"{(reporte.get('descripcion') or '')[:400]}\", "
        f"ubicación: {(reporte.get('ubicacion') or {}).get('nombre')}.\n"
        f"Contrato: objeto: \"{(contrato.get('objeto') or contrato.get('texto_original') or '')[:400]}\", "
        f"municipio: {contrato.get('municipio_nombre')}.\n"
        f"Señales que ya detectaron las reglas: {', '.join(senales) or 'ninguna'}.\n"
        f"Explicación técnica de las reglas: \"{evidencia_reglas}\"."
    )
    texto = llamar_ia(SISTEMA, contexto, max_tokens=220)
    if not texto:
        return None
    texto = texto.strip()
    return texto or None
