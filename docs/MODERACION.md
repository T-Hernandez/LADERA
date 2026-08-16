# Moderación

Un reporte es contenido generado por un usuario, no un hecho verificado
(`Plan.md`, 1.3). Este documento define cómo LADERA evita que eso destruya su
credibilidad, sin convertirse en un sistema de censura editorial.

## Estados de un reporte (Fase 10)

```text
BORRADOR      no enviado, no aparece en el mapa
EN_REVISION   enviado; observación, no hecho verificado
PUBLICADO     a la vista; eso no lo vuelve verdadero
RELACIONADO   hay un vínculo con contratación; el vínculo no lo verifica
VERIFICADO    una persona lo revisó; no declara que el problema sea cierto
DESCARTADO    fuera de la superficie pública; el registro no se borra
RETIRADO      retirado; ya no aparece como observación pública
```

Transiciones permitidas y frase que explica cada estado:
`reportes/confianza.py` (`TRANSICIONES`, `FRASES`). `DESCARTADO`, `RETIRADO` y
`BORRADOR` no salen al mapa ni a la búsqueda
(`modelo/constantes.py:ESTADOS_REPORTE_VISIBLES`).

## Filtros al crear (Fase 10 + 1.4)

Antes de guardar un reporte, `reportes/almacen.py` aplica, en orden:

```text
1. rechazo_contenido      texto mínimo, no es solo un enlace, no es ruido repetido
2. exceso_frecuencia       límite de reportes por actor en una ventana de tiempo
3. es_duplicado             misma descripción, mismo municipio, ventana reciente
```

- `rechazo_contenido` (`reportes/contenido.py`) rechaza texto vacío, muy
  corto, sin letras reales, un enlace solo, o ruido tipo `asdfasdf`. No es un
  filtro político ni de contenido ofensivo: solo exige que el texto describa
  algo.
- `exceso_frecuencia` y `es_duplicado` (`reportes/confianza.py`) leen la
  auditoría y los reportes existentes; no hardcodean umbrales de negocio en
  el modelo (ver `config.py`).

Ninguno de los tres se apoya en IA. Si algún filtro rechaza el envío, la
persona ve el motivo y puede corregir el texto.

## Señalamiento y revisión administrativa

```text
POST /api/reportes/<id>/senalar    cualquiera puede señalar contenido
POST /api/reportes/<id>/revisar    mueve el estado con motivo (≥10 caracteres)
POST /api/reportes/<id>/retirar    atajo de revisar → RETIRADO
```

`senalar_reporte` cuenta señalamientos por reporte. Al llegar al umbral
(`config.SENALAMIENTOS_PARA_REVISION`), el sistema —no una persona— empuja el
reporte de vuelta a `EN_REVISION` con actor `"sistema"` y motivo automático.
Los señalamientos nunca descartan ni retiran un reporte por sí solos: solo lo
regresan a revisión humana.

Toda transición exige `motivo` explícito y respeta `TRANSICIONES`; un salto no
listado (por ejemplo `BORRADOR → VERIFICADO`) lanza `ReporteError`.

## El límite de la IA en moderación

```text
la IA no puede pasar un reporte a VERIFICADO
```

`revisar_reporte` rechaza la transición si el actor es reconocible como IA
(`_es_ia`, por nombre: `ia`, `modelo`, `llm`, `asistente`). Verificar es
siempre un acto humano. La IA tampoco participa en `senalar_reporte` ni en
`rechazo_contenido`: son reglas explícitas, no un modelo.

## Auditoría (Fase 10, 5.2)

Toda acción sensible —crear, señalar, revisar, retirar— se registra en
`data/interim/auditoria.json` vía `reportes/auditoria.py`:

```text
actor
acción
fecha
objeto {tipo, id}
resultado
motivo
```

`reportes/confianza.py:explicar_estado` compone, a partir de esa bitácora, la
respuesta a la pregunta que exige el criterio de aceptación de la Fase 10:

> ¿Por qué este reporte tiene este estado?

Se expone en `GET /api/reportes/<id>/confianza` y se muestra en el panel del
reporte, junto con el conteo de señalamientos y la última decisión.

## Qué no hace la moderación

- No borra reportes físicamente: `DESCARTADO` y `RETIRADO` dejan de ser
  visibles, pero el registro y su auditoría permanecen.
- No crea cuentas de moderador ni roles administrativos separados: cualquier
  actor puede revisar si conoce la ruta; el rastro queda en la auditoría, no
  en un permiso.
- No deja que tres señalamientos descarten solos un contenido: el umbral
  regresa el reporte a revisión, no lo elimina.
- No usa la IA como fuente de verdad de ningún estado (ver
  `docs/TRAZABILIDAD.md`, "Lo que no se afirma").
