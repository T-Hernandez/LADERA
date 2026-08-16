"""Escala extensible. El piloto no se ensancha solo."""

from escala.activar import EscalaError, estado_escala, intentar_activar
from escala.puerta import evaluar_puerta

__all__ = ["EscalaError", "estado_escala", "evaluar_puerta", "intentar_activar"]
