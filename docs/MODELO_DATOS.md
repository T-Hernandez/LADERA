# Modelo de datos — Fase 1

Este es el contrato que consume el frontend. Cambiar un campo aquí implica
cambiar `datos.json` y la interfaz. No al revés.

## Unidades

```text
CONTRATO     registro público (hoy: fixture; después: SECOP II)
REPORTE      observación ciudadana
EVIDENCIA    archivo o URL que acompaña un reporte
UBICACIÓN    municipio (DANE) y, si existe, un lugar más específico
RELACIÓN     vínculo entre un reporte y un contrato
FUENTE       de dónde salió cada dato mostrado
```

## Municipio

Clave: código DANE de 5 dígitos (`05001`).

| Campo         | Tipo     | Notas                                      |
| ------------- | -------- | ------------------------------------------ |
| `nombre`      | string   | Nombre oficial                             |
| `dane`        | string   | Igual a la clave                           |
| `contratos`   | int      | Conteo. Un contrato sin cifra también cuenta |
| `reportes`    | int      | Conteo de reportes en ese municipio        |
| `plata_total` | number   | Suma solo de valores utilizables           |
| `contrato_ids`| string[] |                                            |
| `reporte_ids` | string[] |                                            |

Los 125 municipios de Antioquia existen siempre. Ausencia = ceros y listas vacías, no una clave faltante.

## Contrato

| Campo            | Tipo            | Notas                                      |
| ---------------- | --------------- | ------------------------------------------ |
| `id`             | string          | Identidad. Nunca el nombre de la entidad   |
| `fuente`         | string          | `fixture` o `secop2`                       |
| `url_fuente`     | string \| null  | `URLProceso` del dataset. No se inventa    |
| `objeto`         | string          |                                            |
| `entidad`        | string          |                                            |
| `contratista`    | string \| null  |                                            |
| `valor`          | number \| null  | `null` si no es utilizable                 |
| `valor_motivo`   | string \| null  | Por qué no suma, si `valor` es `null`      |
| `fecha_firma`    | string \| null  | ISO `YYYY-MM-DD`                           |
| `fecha_inicio`   | string \| null  |                                            |
| `fecha_fin`      | string \| null  |                                            |
| `estado`         | string          | `ACTIVO` `FINALIZADO` `PROXIMO_A_VENCER` `SIN_FECHA_SUFICIENTE` `DESCONOCIDO` |
| `municipio_dane` | string          |                                            |
| `municipio_nombre` | string        |                                            |
| `ubicaciones`    | object[]        | Ver abajo                                  |
| `texto_original` | string          | Texto del que se extrae cualquier fragmento |

### Ubicación de un contrato

```text
nombre
fragmento     literalmente presente en texto_original
fuente
```

Sin fragmento verificable, la ubicación submunicipal no se muestra.

## Reporte

| Campo              | Tipo     | Notas                                      |
| ------------------ | -------- | ------------------------------------------ |
| `id`               | string   |                                            |
| `fecha_creacion`   | string   | ISO datetime                               |
| `fecha_observacion`| string   | Fecha en que ocurrió lo observado          |
| `descripcion`      | string   | Qué observó la persona                     |
| `categoria`        | string   | `OBRA_INCONCLUSA` `OBRA_DETERIORADA` `OBRA_NO_VISIBLE` `PROBLEMA_PERSISTENTE` `RIESGO` `OTRO` |
| `estado`           | string   | `PUBLICADO` `EN_REVISION` `RELACIONADO` `VERIFICADO` `DESCARTADO` |
| `autor`            | string   | Etiqueta. No es una identidad verificada   |
| `ubicacion`        | object   | `dane`, `nombre`, `detalle`, `lat`, `lng`  |
| `evidencias`       | object[] |                                            |

Un reporte es una observación, no un hecho verificado.

## Evidencia

| Campo      | Tipo   |
| ---------- | ------ |
| `id`       | string |
| `tipo`     | `foto` `url` `nota` |
| `url`      | string |
| `fecha`    | string |
| `metadata` | object |

## Relación

Nunca es solo `{contrato_id, reporte_id}`.

| Campo           | Tipo            |
| --------------- | --------------- |
| `id`            | string          |
| `origen`        | `{tipo, id}`    |
| `destino`       | `{tipo, id}`    |
| `tipo_relacion` | `DIRECTA` `TERRITORIAL` `TEMPORAL` `SEMANTICA` `COMPUESTA` |
| `metodo`        | `DIRECTA` `REGLAS` `IA` `MANUAL` |
| `confianza`     | number \| null  |
| `estado`        | `SUGERIDA` `CONFIRMADA` `DESCARTADA` |
| `evidencia`     | string          | Por qué se sugirió, en lenguaje concreto |
| `creado_en`     | string          |
| `revisado_en`   | string \| null  |

`SUGERIDA` no se pinta como hecho. La IA no puede crear una `CONFIRMADA`.

## Archivo canónico

```text
data/fixtures/datos.json
```

```json
{
  "resumen": {},
  "municipios": {},
  "contratos": {},
  "reportes": {},
  "relaciones": []
}
```

El frontend no recalcula agregados. Solo formatea, filtra y navega.
