"""IA opcional: solo puede devolver el JSON de filtros. Si falla, no hay resultados inventados."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from busqueda.consulta import validar_consulta

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


def interpretar_con_ia(pregunta: str, dane_zona: str | None = None) -> dict | None:
    clave = os.environ.get("LADERA_IA_CLAVE")
    url = os.environ.get("LADERA_IA_URL")
    if not clave or not url:
        return None
    contexto = f" Municipio abierto (territorio_dane): {dane_zona}." if dane_zona else ""
    cuerpo = json.dumps(
        {
            "messages": [
                {"role": "system", "content": "Solo JSON de filtros. Sin prosa. No inventes contratos, reportes ni URLs."},
                {"role": "user", "content": PROMPT + pregunta + contexto},
            ]
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=cuerpo,
        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    texto = None
    if isinstance(payload, dict):
        choices = payload.get("choices") or []
        if choices:
            texto = (choices[0].get("message") or {}).get("content")
        texto = texto or payload.get("content")
    if not texto:
        return None
    crudo = _json_de(texto)
    if not crudo:
        return None
    try:
        return validar_consulta(crudo)
    except ValueError:
        return None
