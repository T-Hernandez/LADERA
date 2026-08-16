"""Intentar ensanchar. El producto vivo no cambia de capa."""

from __future__ import annotations

from escala.ejes import catalogo_ejes
from escala.puerta import evaluar_puerta

MAPA_ACTIVO = "municipios_antioquia.geojson"

DESTINOS_BLOQUEADOS = {
    ("territorio", "region"): "no hay capa recortada de región; no se carga la capa nacional en el navegador",
    ("territorio", "pais"): "no se abre el país; no se carga co_2018_MGN_MPIO_POLITICO.geojson",
    ("fuentes", "documentos"): "no hay una fuente de documentos cableada; no se inventan URLs",
    ("fuentes", "presupuestos"): "no hay presupuestos en el conjunto; no se estiman",
    ("fuentes", "otras"): "otra fuente pública se declara, no se adivina",
    ("comunidad", "organizaciones"): "no hay cuentas de organización; el reporte sigue siendo una observación",
    ("comunidad", "periodistas"): "no hay un rol aparte de periodista en este producto",
    ("comunidad", "investigadores"): "no hay un rol aparte de investigador en este producto",
    ("comunidad", "comunidades"): "la comunidad local ya observa; no se finge una red nacional",
}


class EscalaError(ValueError):
    pass


def estado_escala(datos: dict, *, ruta_eventos=None, ruta_auditoria=None) -> dict:
    puerta = evaluar_puerta(datos, ruta_eventos=ruta_eventos, ruta_auditoria=ruta_auditoria)
    return {
        "ejes": catalogo_ejes(),
        "puerta": puerta,
        "mapa_activo": MAPA_ACTIVO,
        "territorio_activo": "Antioquia",
        "nota": (
            "La infraestructura ya puede nombrar el siguiente paso en territorio, "
            "fuentes y comunidad. Nombrarlo no lo enciende. "
            "El mapa sigue siendo el recorte de Antioquia."
        ),
    }


def intentar_activar(eje: str, destino: str, datos: dict, *, ruta_eventos=None, ruta_auditoria=None) -> dict:
    eje = (eje or "").strip()
    destino = (destino or "").strip()
    estado = estado_escala(datos, ruta_eventos=ruta_eventos, ruta_auditoria=ruta_auditoria)
    catalogo = {item["id"]: item for item in estado["ejes"]}
    if eje not in catalogo:
        raise EscalaError("eje de escala no reconocido")
    if destino not in catalogo[eje]["pasos"]:
        raise EscalaError("ese paso no existe en el eje")
    if destino == catalogo[eje]["actual"]:
        raise EscalaError("ese paso ya es el alcance actual")
    if not estado["puerta"]["listos"]:
        faltan = [c for c, d in estado["puerta"]["detalle"].items() if not d["ok"]]
        raise EscalaError(
            "no se escala solo porque es posible; faltan: " + ", ".join(faltan)
        )
    motivo = DESTINOS_BLOQUEADOS.get((eje, destino))
    if motivo:
        raise EscalaError(motivo)
    raise EscalaError("el siguiente paso no tiene datos recortados en este producto")
