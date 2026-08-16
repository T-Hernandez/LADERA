"""Fase 4: curar el crudo en local. No inventa correcciones ni vuelve a descargar."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from config import (  # noqa: E402
    CURACION_EXCLUIDOS,
    CURACION_LIMPIO,
    CURACION_MANIFIESTO,
    CURACION_REPORTE,
    CURACION_REVISAR,
    DIAS_PROXIMO_A_VENCER,
    DIR_FINAL,
    DIR_INTERIM,
    DIR_RAW,
    MANIFIESTO,
    SECOP_COLUMNAS,
    VALOR_MINIMO_USABLE,
)

CAMPOS_EXTRA = (
    "destino",
    "motivo_destino",
    "valor_clase",
    "valor_usable",
    "valor_motivo",
    "estado_normalizado",
    "fecha_firma_norm",
    "fecha_inicio_norm",
    "fecha_fin_norm",
)

ESTADOS_SECOP = {
    "en ejecucion": "ACTIVO",
    "modificado": "ACTIVO",
    "suspendido": "ACTIVO",
    "cedido": "ACTIVO",
    "aprobado": "ACTIVO",
    "terminado": "FINALIZADO",
    "cerrado": "FINALIZADO",
    "cancelado": "DESCONOCIDO",
}


class CuracionError(RuntimeError):
    pass


def norm(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", str(texto or ""))
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.casefold().split())


def parse_fecha(valor: str | None) -> date | None:
    crudo = (valor or "").strip()
    if not crudo:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(crudo[:26], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(crudo[:10])
    except ValueError:
        return None


def parse_valor(crudo: str | None) -> tuple[float | None, str | None]:
    texto = (crudo or "").strip()
    if not texto:
        return None, "valor ausente"
    try:
        numero = float(texto)
    except ValueError:
        return None, "valor no numerico"
    if numero < 0:
        return None, "valor negativo"
    return numero, None


def clasificar_valor(numero: float | None, motivo_parse: str | None, minimo: int) -> tuple[str, float | None, str | None]:
    if motivo_parse:
        return "NO_UTILIZABLE", None, motivo_parse
    assert numero is not None
    if numero == 0:
        return "NO_UTILIZABLE", None, "valor en cero"
    if 0 < numero < minimo:
        return "REVISAR", None, f"valor por debajo del umbral minimo ({minimo})"
    return "UTILIZABLE", numero, None


def normalizar_estado(estado_secop: str, fecha_fin: date | None, hoy: date, dias_vence: int) -> str:
    base = ESTADOS_SECOP.get(norm(estado_secop), "DESCONOCIDO")
    if base == "ACTIVO":
        if fecha_fin is None:
            return "SIN_FECHA_SUFICIENTE"
        if hoy <= fecha_fin <= hoy + timedelta(days=dias_vence):
            return "PROXIMO_A_VENCER"
    return base


def curar_fila(
    fila: dict,
    *,
    vistos: set[str],
    hoy: date,
    minimo: int = VALOR_MINIMO_USABLE,
    dias_vence: int = DIAS_PROXIMO_A_VENCER,
) -> dict:
    ident = (fila.get("id_contrato") or "").strip()
    objeto = (fila.get("objeto_del_contrato") or "").strip()
    destino = "LIMPIO"
    motivo_destino = ""

    if not ident:
        destino, motivo_destino = "EXCLUIDO", "sin id_contrato"
    elif ident in vistos:
        destino, motivo_destino = "EXCLUIDO", "id_contrato duplicado"
    elif not objeto:
        destino, motivo_destino = "EXCLUIDO", "sin objeto contractual"
    elif norm(objeto) in {"prueba", "test"}:
        destino, motivo_destino = "EXCLUIDO", "objeto de prueba"

    if ident and destino != "EXCLUIDO":
        vistos.add(ident)

    numero, motivo_parse = parse_valor(fila.get("valor_del_contrato"))
    valor_clase, valor_usable, valor_motivo = clasificar_valor(numero, motivo_parse, minimo)
    if destino == "LIMPIO" and valor_clase == "REVISAR":
        destino = "REVISAR"
        motivo_destino = valor_motivo or "valor para revisar a mano"

    fecha_firma = parse_fecha(fila.get("fecha_de_firma"))
    fecha_inicio = parse_fecha(fila.get("fecha_de_inicio_del_contrato"))
    fecha_fin = parse_fecha(fila.get("fecha_de_fin_del_contrato"))
    estado = normalizar_estado(fila.get("estado_contrato") or "", fecha_fin, hoy, dias_vence)

    salida = {col: fila.get(col, "") for col in SECOP_COLUMNAS}
    salida.update(
        {
            "destino": destino,
            "motivo_destino": motivo_destino,
            "valor_clase": valor_clase,
            "valor_usable": "" if valor_usable is None else f"{valor_usable:.0f}",
            "valor_motivo": valor_motivo or "",
            "estado_normalizado": estado,
            "fecha_firma_norm": fecha_firma.isoformat() if fecha_firma else "",
            "fecha_inicio_norm": fecha_inicio.isoformat() if fecha_inicio else "",
            "fecha_fin_norm": fecha_fin.isoformat() if fecha_fin else "",
        }
    )
    return salida


def _hash_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def resolver_entrada(entrada: Path | None) -> Path:
    if entrada:
        if not entrada.exists():
            raise CuracionError(f"no existe {entrada}")
        return entrada
    if MANIFIESTO.exists():
        doc = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
        actual = (doc or {}).get("actual") or {}
        if actual.get("archivo"):
            ruta = RAIZ / actual["archivo"]
            if ruta.exists():
                return ruta
    candidatos = sorted(DIR_RAW.glob("contratos_*.csv"))
    if not candidatos:
        raise CuracionError("no hay un crudo en data/raw. Corre la Fase 3 primero.")
    return candidatos[-1]


def curar(
    entrada: Path | None = None,
    *,
    limpio: Path = CURACION_LIMPIO,
    revisar: Path = CURACION_REVISAR,
    excluidos: Path = CURACION_EXCLUIDOS,
    reporte: Path = CURACION_REPORTE,
    manifiesto: Path = CURACION_MANIFIESTO,
    hoy: date | None = None,
) -> dict:
    origen = resolver_entrada(entrada)
    hoy = hoy or date.today()
    with origen.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        raise CuracionError(f"{origen} está vacío")

    vistos: set[str] = set()
    curadas = [curar_fila(fila, vistos=vistos, hoy=hoy) for fila in filas]
    por_destino = {"LIMPIO": [], "REVISAR": [], "EXCLUIDO": []}
    for fila in curadas:
        por_destino[fila["destino"]].append(fila)

    DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    DIR_FINAL.mkdir(parents=True, exist_ok=True)
    campos = list(SECOP_COLUMNAS) + list(CAMPOS_EXTRA)
    for ruta, dest in (
        (limpio, "LIMPIO"),
        (revisar, "REVISAR"),
        (excluidos, "EXCLUIDO"),
    ):
        with ruta.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(por_destino[dest])

    limpios = por_destino["LIMPIO"]
    plata = sum(int(f["valor_usable"]) for f in limpios if f["valor_usable"])
    resumen = {
        "entrada": str(origen.relative_to(RAIZ)).replace("\\", "/") if origen.is_relative_to(RAIZ) else str(origen),
        "hash_entrada": _hash_archivo(origen),
        "fecha": hoy.isoformat(),
        "filas": len(filas),
        "ids_unicos": len({(f.get("id_contrato") or "").strip() for f in filas if (f.get("id_contrato") or "").strip()}),
        "LIMPIO": len(por_destino["LIMPIO"]),
        "REVISAR": len(por_destino["REVISAR"]),
        "EXCLUIDO": len(por_destino["EXCLUIDO"]),
        "valor_utilizable": sum(1 for f in limpios if f["valor_clase"] == "UTILIZABLE"),
        "valor_no_utilizable": sum(1 for f in limpios if f["valor_clase"] == "NO_UTILIZABLE"),
        "plata_usable": plata,
        "estados": dict(Counter(f["estado_normalizado"] for f in limpios)),
        "motivos_excluido": dict(Counter(f["motivo_destino"] for f in por_destino["EXCLUIDO"])),
        "motivos_revisar": dict(Counter(f["motivo_destino"] for f in por_destino["REVISAR"])),
    }
    texto = [
        "LADERA — reporte de curación (Fase 4)",
        f"entrada: {resumen['entrada']}",
        f"hash: {resumen['hash_entrada']}",
        f"filas: {resumen['filas']}",
        f"ids unicos: {resumen['ids_unicos']}",
        f"LIMPIO: {resumen['LIMPIO']}",
        f"REVISAR: {resumen['REVISAR']}",
        f"EXCLUIDO: {resumen['EXCLUIDO']}",
        f"con cifra usable: {resumen['valor_utilizable']}",
        f"sin cifra usable (siguen contando): {resumen['valor_no_utilizable']}",
        f"plata usable: {resumen['plata_usable']}",
        f"estados: {resumen['estados']}",
        f"motivos excluido: {resumen['motivos_excluido']}",
        f"motivos revisar: {resumen['motivos_revisar']}",
        "",
        "Un contrato en REVISAR o sin cifra usable sigue existiendo.",
        "No se reemplazó ningún valor por una estimación.",
        "Para saber por qué un id no suma: buscalo en contratos_revisar.csv o contratos_excluidos.csv.",
    ]
    reporte.write_text("\n".join(texto) + "\n", encoding="utf-8")
    manifiesto.parent.mkdir(parents=True, exist_ok=True)
    manifiesto.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(texto[:12]))
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cura el crudo de SECOP en local.")
    parser.add_argument("--entrada", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        curar(args.entrada)
        return 0
    except CuracionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
