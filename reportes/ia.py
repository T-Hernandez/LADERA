"""IA opcional para el proceso de reportes: sugiere, nunca decide.

- sugerir_categoria: ayuda al ciudadano a elegir la categoría de su
  observación a partir de lo que escribió. Es una sugerencia editable, no
  se aplica sola — el ciudadano sigue eligiendo la categoría final.
- evaluar_riesgo: da al moderador una pista de prioridad antes de que decida
  revisar/retirar. No aprueba, no rechaza, no reemplaza el motivo que el
  moderador debe escribir para su propia decisión.
"""

from __future__ import annotations

from ia_cliente import extraer_json, llamar_ia
from modelo.constantes import CATEGORIAS_REPORTE

SISTEMA_CATEGORIA = (
    "Clasificas descripciones ciudadanas de problemas de obras públicas en "
    "Colombia. Respondes SOLO un objeto JSON: "
    '{"categoria": "...", "motivo": "..."}. '
    "categoria debe ser EXACTAMENTE una de estas palabras: OBRA_INCONCLUSA, "
    "OBRA_DETERIORADA, OBRA_NO_VISIBLE, PROBLEMA_PERSISTENTE, RIESGO, OTRO. "
    "motivo: una frase corta en español explicando la elección, basada solo "
    "en lo que dice el texto. No inventes hechos que el texto no menciona."
)

SISTEMA_RIESGO = (
    "Evalúas, para un moderador humano, qué tan prioritario es revisar una "
    "observación ciudadana antes que otras — nunca si es verdadera o falsa. "
    "Respondes SOLO un objeto JSON: "
    '{"nivel": "...", "motivo": "..."}. '
    "nivel debe ser EXACTAMENTE una de: BAJA, MEDIA, ALTA. "
    "ALTA solo si el texto describe un riesgo físico inminente (derrumbe, "
    "colapso, estructura que puede ceder). MEDIA para daños o incumplimientos "
    "sin urgencia inmediata. BAJA para el resto. motivo: una frase corta en "
    "español. No decides si el reporte es verdadero, solo la urgencia de "
    "mirarlo primero."
)

_NIVELES_RIESGO = frozenset({"BAJA", "MEDIA", "ALTA"})


def sugerir_categoria(descripcion: str) -> dict | None:
    descripcion = (descripcion or "").strip()
    if len(descripcion) < 15:
        return None
    texto = llamar_ia(SISTEMA_CATEGORIA, descripcion, max_tokens=150)
    if not texto:
        return None
    crudo = extraer_json(texto)
    if not crudo:
        return None
    categoria = crudo.get("categoria")
    if categoria not in CATEGORIAS_REPORTE:
        return None
    motivo = str(crudo.get("motivo") or "").strip()[:240]
    return {"categoria": categoria, "motivo": motivo}


def evaluar_riesgo(descripcion: str) -> dict | None:
    descripcion = (descripcion or "").strip()
    if len(descripcion) < 15:
        return None
    texto = llamar_ia(SISTEMA_RIESGO, descripcion, max_tokens=150)
    if not texto:
        return None
    crudo = extraer_json(texto)
    if not crudo:
        return None
    nivel = crudo.get("nivel")
    if nivel not in _NIVELES_RIESGO:
        return None
    motivo = str(crudo.get("motivo") or "").strip()[:240]
    return {"nivel": nivel, "motivo": motivo}
