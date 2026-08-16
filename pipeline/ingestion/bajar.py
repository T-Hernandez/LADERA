"""Fase 3: descarga cruda de SECOP II. La red solo se toca aquí."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    DIR_METADATA,
    DIR_RAW,
    MANIFIESTO,
    SECOP_APP_TOKEN,
    SECOP_COLUMNAS,
    SECOP_DATASET,
    SECOP_FUENTE,
    SECOP_LIMIT,
    SECOP_RECURSO,
    SECOP_TIMEOUT,
    SECOP_WHERE,
)


class IngestaError(RuntimeError):
    """La descarga no produjo un crudo utilizable."""


def http_get(url: str, timeout: int, token: str | None) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "LADERA/fase3 (datos.gov.co)",
        },
    )
    if token:
        req.add_header("X-App-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        cuerpo = exc.read().decode("utf-8", errors="replace")
        return exc.code, cuerpo
    except urllib.error.URLError as exc:
        raise IngestaError(f"fallo de red o timeout: {exc.reason}") from exc


def url_pagina(offset: int, limit: int, where: str) -> str:
    params = {
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": ":id",
        "$select": ",".join(SECOP_COLUMNAS),
        "$where": where,
    }
    return f"{SECOP_RECURSO}?{urllib.parse.urlencode(params)}"


def aplanar(fila: dict) -> dict:
    plano = {}
    for col in SECOP_COLUMNAS:
        valor = fila.get(col)
        if col == "urlproceso" and isinstance(valor, dict):
            valor = valor.get("url")
        plano[col] = valor
    return plano


def leer_pagina(offset: int, limit: int, where: str, obtener, timeout: int, token: str | None) -> list[dict]:
    url = url_pagina(offset, limit, where)
    estado, cuerpo = obtener(url, timeout, token)
    if estado != 200:
        raise IngestaError(f"HTTP {estado} en offset {offset}: {cuerpo[:240]}")
    try:
        datos = json.loads(cuerpo)
    except json.JSONDecodeError as exc:
        raise IngestaError(f"respuesta corrupta en offset {offset}") from exc
    if not isinstance(datos, list):
        raise IngestaError(f"se esperaba una lista en offset {offset}")
    for fila in datos:
        if not fila.get("id_contrato"):
            raise IngestaError("una fila llegó sin id_contrato; no se guarda el crudo")
    return datos


def contar(obtener=http_get, where: str = SECOP_WHERE, timeout: int = SECOP_TIMEOUT, token: str | None = SECOP_APP_TOKEN) -> int:
    params = {"$select": "count(*)", "$where": where}
    url = f"{SECOP_RECURSO}?{urllib.parse.urlencode(params)}"
    estado, cuerpo = obtener(url, timeout, token)
    if estado != 200:
        raise IngestaError(f"HTTP {estado} al contar: {cuerpo[:240]}")
    try:
        filas = json.loads(cuerpo)
        return int(filas[0]["count"])
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise IngestaError("no se pudo leer el conteo") from exc


def _hash_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _leer_manifiesto(ruta: Path) -> dict:
    if not ruta.exists():
        return {"actual": None, "historial": []}
    return json.loads(ruta.read_text(encoding="utf-8"))


def _guardar_manifiesto(entrada: dict, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc = _leer_manifiesto(ruta)
    if doc.get("actual") and entrada["estado"] == "OK":
        doc.setdefault("historial", []).append(doc["actual"])
    if entrada["estado"] == "OK":
        doc["actual"] = entrada
    else:
        doc.setdefault("historial", []).append(entrada)
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def descargar(
    *,
    obtener=http_get,
    where: str = SECOP_WHERE,
    limit: int = SECOP_LIMIT,
    timeout: int = SECOP_TIMEOUT,
    token: str | None = SECOP_APP_TOKEN,
    destino: Path | None = None,
    manifiesto: Path | None = None,
    forzar: bool = False,
    max_paginas: int | None = None,
    hoy: date | None = None,
) -> dict:
    DIR_RAW.mkdir(parents=True, exist_ok=True)
    dia = hoy or date.today()
    destino = destino or (DIR_RAW / f"contratos_{dia.isoformat()}.csv")
    manifiesto = manifiesto or MANIFIESTO
    if destino.exists() and not forzar:
        raise IngestaError(
            f"ya existe {destino.name}. No se sobrescribe. Usa --force para archivar el anterior."
        )

    inicio = time.monotonic()
    consulta = {
        "recurso": SECOP_RECURSO,
        "dataset": SECOP_DATASET,
        "where": where,
        "order": ":id",
        "limit": limit,
        "columnas": list(SECOP_COLUMNAS),
    }
    filas: list[dict] = []
    offset = 0
    paginas = 0
    try:
        while True:
            if max_paginas is not None and paginas >= max_paginas:
                raise IngestaError("se alcanzó max_paginas; eso no es una descarga completa")
            lote = leer_pagina(offset, limit, where, obtener, timeout, token)
            paginas += 1
            print(f"pagina {paginas}: offset={offset} filas={len(lote)} acumulado={len(filas) + len(lote)}")
            if not lote:
                break
            filas.extend(lote)
            if len(lote) < limit:
                break
            offset += limit
        if not filas:
            raise IngestaError("la consulta devolvió cero contratos")

        temporal = destino.with_name(destino.name + ".tmp")
        with temporal.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(SECOP_COLUMNAS), extrasaction="ignore")
            writer.writeheader()
            for fila in filas:
                writer.writerow(aplanar(fila))

        if destino.exists() and forzar:
            respaldo = destino.with_name(
                f"{destino.stem}_reemplazado_{_hash_archivo(destino)[:8]}.csv"
            )
            destino.replace(respaldo)
        temporal.replace(destino)
    except IngestaError as exc:
        entrada = {
            "fuente": SECOP_FUENTE,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "consulta": consulta,
            "cantidad_descargada": len(filas),
            "duracion_segundos": round(time.monotonic() - inicio, 2),
            "estado": "FALLO",
            "hash": None,
            "archivo": None,
            "error": str(exc),
        }
        _guardar_manifiesto(entrada, manifiesto)
        raise

    entrada = {
        "fuente": SECOP_FUENTE,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "consulta": consulta,
        "cantidad_descargada": len(filas),
        "duracion_segundos": round(time.monotonic() - inicio, 2),
        "estado": "OK",
        "hash": _hash_archivo(destino),
        "archivo": (
            str(destino.relative_to(RAIZ)).replace("\\", "/")
            if destino.is_relative_to(RAIZ)
            else str(destino)
        ),
    }
    _guardar_manifiesto(entrada, manifiesto)
    print(f"OK {entrada['cantidad_descargada']} contratos -> {entrada['archivo']}")
    print(f"hash {entrada['hash']}")
    return entrada


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descarga el crudo de SECOP II (datos.gov.co).")
    parser.add_argument("--force", action="store_true", help="archiva el CSV del mismo día y vuelve a bajar")
    parser.add_argument("--solo-contar", action="store_true", help="consulta el conteo y no descarga")
    args = parser.parse_args(argv)
    try:
        if args.solo_contar:
            total = contar()
            print(f"{total} contratos en la consulta piloto")
            return 0
        descargar(forzar=args.force)
        return 0
    except IngestaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
