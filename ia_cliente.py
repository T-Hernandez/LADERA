"""Cliente compartido para llamar a la IA (API de Groq, formato chat completions).

Todo lo que usa este cliente sigue la misma regla: la IA solo puede devolver
texto/JSON que quien llama valida antes de usar. Nunca decide nada por sí
sola, nunca se le da la última palabra, y cualquier fallo (sin clave, sin
red, JSON inválido) se resuelve devolviendo None — quien llama cae de vuelta
a un comportamiento sin IA.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import IA_CLAVE, IA_MODELO, IA_URL


def ia_configurada() -> bool:
    return bool(IA_CLAVE)


def llamar_ia(sistema: str, usuario: str, *, max_tokens: int = 300) -> str | None:
    """Llama a Groq y devuelve el texto de la respuesta, o None si algo falla."""
    if not IA_CLAVE:
        return None
    cuerpo = json.dumps(
        {
            "model": IA_MODELO,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        IA_URL,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {IA_CLAVE}",
            "Content-Type": "application/json",
            # Sin un User-Agent de navegador, el Cloudflare frente a la API de
            # Groq responde 403 antes de que la petición llegue a Groq.
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
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    mensaje = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(mensaje, dict):
        return None
    contenido = mensaje.get("content")
    return contenido if isinstance(contenido, str) and contenido.strip() else None


def extraer_json(texto: str) -> dict | None:
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
