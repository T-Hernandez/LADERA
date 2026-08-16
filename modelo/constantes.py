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
SENALES_RELACION = frozenset({"TERRITORIAL", "TEMPORAL", "SEMANTICA"})

# Clasificación de calidad que ya calcula pipeline/processing/curar.py (Fase 4)
VALOR_CLASE = frozenset({"UTILIZABLE", "NO_UTILIZABLE", "REVISAR"})
# Clasificación que ya calcula pipeline/processing/resolver.py (Fase 5)
RESOLUCION_TERRITORIO = frozenset(
    {"OBJETO", "CIUDAD_ENTIDAD", "MULTIMUNICIPIO", "AMBIGUO", "SIN_RESOLVER"}
)
