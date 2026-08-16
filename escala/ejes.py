"""Los tres ejes del plan. Nombrar el siguiente paso no lo activa."""

EJES = (
    {
        "id": "territorio",
        "pasos": ("municipio", "departamento", "region", "pais"),
        "actual": "departamento",
        "valor": "Antioquia",
        "siguiente": "region",
    },
    {
        "id": "fuentes",
        "pasos": ("contratacion", "documentos", "presupuestos", "otras"),
        "actual": "contratacion",
        "valor": "SECOP II vía datos.gov.co (jbjy-vk9h); el mapa sigue en fixture",
        "siguiente": "documentos",
    },
    {
        "id": "comunidad",
        "pasos": ("usuarios", "organizaciones", "periodistas", "investigadores", "comunidades"),
        "actual": "usuarios",
        "valor": "observaciones ciudadanas locales",
        "siguiente": "organizaciones",
    },
)


def catalogo_ejes() -> list[dict]:
    return [dict(eje) for eje in EJES]
