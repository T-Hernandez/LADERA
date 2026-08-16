MUNICIPIOS_ESPERADOS = 125

FUENTES = frozenset({"fixture", "secop2"})
ESTADOS_CONTRATO = frozenset(
    {
        "ACTIVO",
        "FINALIZADO",
        "PROXIMO_A_VENCER",
        "SIN_FECHA_SUFICIENTE",
        "DESCONOCIDO",
    }
)
CATEGORIAS_REPORTE = frozenset(
    {
        "OBRA_INCONCLUSA",
        "OBRA_DETERIORADA",
        "OBRA_NO_VISIBLE",
        "PROBLEMA_PERSISTENTE",
        "RIESGO",
        "OTRO",
    }
)
ESTADOS_REPORTE = frozenset(
    {
        "BORRADOR",
        "PUBLICADO",
        "EN_REVISION",
        "RELACIONADO",
        "VERIFICADO",
        "DESCARTADO",
        "RETIRADO",
    }
)
ESTADOS_REPORTE_VISIBLES = frozenset(
    {
        "PUBLICADO",
        "EN_REVISION",
        "RELACIONADO",
        "VERIFICADO",
    }
)
TIPOS_EVIDENCIA = frozenset({"foto", "url", "nota"})
TIPOS_EXTREMO = frozenset({"contrato", "reporte"})
TIPOS_RELACION = frozenset(
    {"DIRECTA", "TERRITORIAL", "TEMPORAL", "SEMANTICA", "COMPUESTA"}
)
METODOS_RELACION = frozenset({"DIRECTA", "REGLAS", "IA", "MANUAL"})
ESTADOS_RELACION = frozenset({"SUGERIDA", "CONFIRMADA", "DESCARTADA"})
