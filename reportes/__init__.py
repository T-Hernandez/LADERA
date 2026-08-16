"""Observaciones ciudadanas. No son hechos verificados ni acusan un contrato."""

from reportes.almacen import crear_observacion, leer_reportes
from reportes.territorio import municipio_en_punto

__all__ = ["crear_observacion", "leer_reportes", "municipio_en_punto"]
