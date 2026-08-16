"""IA opcional (API de Groq, formato chat completions): solo puede devolver el JSON de filtros.

Si la clave falta, la llamada falla o la respuesta no pasa validar_consulta,
no hay resultados inventados: quien llama cae de vuelta a las reglas.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from busqueda.consulta import validar_consulta
from config import IA_CLAVE, IA_MODELO, IA_URL

SISTEMA = (
    "Solo respondes con un objeto JSON de filtros de búsqueda. Nunca prosa, "
    "nunca markdown, nunca inventas contratos, reportes ni URLs."
)

PROMPT = (
    "Devuelve SOLO un JSON con estas claves: territorio, territorio_dane, "
    "estado_contrato, categoria_reporte, periodo (desde, hasta), con_reportes, "
    "con_relacion, texto. No inventes contratos, reportes, URLs ni una respuesta. "
    "estado_contrato: ACTIVO, FINALIZADO, PROXIMO_A_VENCER o null. "
    "categoria_reporte: OBRA_INCONCLUSA, OBRA_DETERIORADA, OBRA_NO_VISIBLE, "
    "PROBLEMA_PERSISTENTE, RIESGO, OTRO o null. "
    "Pregunta: "
)


def _json_de(texto: str) -> dict | None:
    try:
        crudo = json.loads(texto)
        if isinstance(crudo, dict):
            return crudo
    except json.JSONDecodeError:
        pass
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio < 0 or fin <= inicio:
        return None
    try:
        crudo = json.loads(texto[inicio : fin + 1])
    except json.JSONDecodeError:
        return None
    return crudo if isinstance(crudo, dict) else None


def _texto_de_respuesta(payload: dict) -> str | None:
    # Forma de Groq (compatible con chat completions de OpenAI):
    # {"choices": [{"message": {"content": "..."}}]}
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    mensaje = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(mensaje, dict):
        return None
    contenido = mensaje.get("content")
    return contenido if isinstance(contenido, str) and contenido else None


def interpretar_con_ia(pregunta: str, dane_zona: str | None = None) -> dict | None:
    clave = IA_CLAVE
    if not clave:
        return None
    contexto = f" Municipio abierto (territorio_dane): {dane_zona}." if dane_zona else ""
    cuerpo = json.dumps(
        {
            "model": IA_MODELO,
            "temperature": 0,
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": SISTEMA},
                {"role": "user", "content": PROMPT + pregunta + contexto},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        IA_URL,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
            # Sin un User-Agent de navegador, el Cloudflare frente a la API
            # de Groq responde 403 (bloqueo por huella de bot) antes de que
            # la petición llegue a Groq — independiente de si la clave es válida.
            "User-Agent": "Mozilla/5.0 (compatible; LADERA/1.0)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    texto = _texto_de_respuesta(payload)
    if not texto:
        return None
    crudo = _json_de(texto)
    if not crudo:
        return None
    try:
        return validar_consulta(crudo)
    except ValueError:
        return None
