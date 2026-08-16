# Producto

LADERA no es un mapa, más un buscador, más un foro, pegados. Es un solo hilo:
territorio → contratos → periodo → reportes → evidencia → relaciones → seguir
investigando. Este documento define ese hilo y cómo se ve en la interfaz.

## Navegación principal

```text
INICIO      resumen del municipio, piloto y escala (vista "explorar")
ZONA        contratos, periodo y reportes de un municipio (mapa)
OBSERVAR    crear un reporte (vista "reportar")
PREGUNTAR   búsqueda en lenguaje corriente (vista "buscar")
```

Implementado en `web/index.html` (`data-vista`) y `web/app.js`. Cambiar de
pestaña no reinicia la zona activa ni la pregunta: las cuatro vistas leen el
mismo estado.

## El recorrido (Fase 11)

`producto/recorrido.py` arma el hilo para una zona:

```text
1. problema     ¿qué se busca? (pregunta o clic en el mapa)
2. zona         municipio identificado
3. contratos    contratos del municipio
4. periodo      filtro de año / estado contractual
5. reportes     reportes ciudadanos del municipio
6. evidencia    al menos un reporte con foto
7. relaciones   vínculos activos (no descartados) entre reporte y contrato
8. continuar    hay relación, o hay contratos y reportes para seguir cruzando
```

Cada paso tiene un booleano `listo`. El backend calcula además `siguiente`: el
primer paso pendiente que tiene sentido ofrecer (`zona` si no hay municipio,
`evidencia` si no hay reportes, `relaciones` si no hay vínculos, `continuar` en
otro caso). El frontend no decide el siguiente paso; lo pide a
`/api/recorrido`.

Toda respuesta del recorrido lleva la misma nota:

> Cero contratos identificados no significa cero inversión. Una relación
> sugerida no verifica el reporte ni declara irregularidad. Otra persona puede
> seguir contrastando desde esta misma zona.

## Regla de producto

Antes de agregar una funcionalidad, debe responder al menos una pregunta:

```text
¿Hace más fácil entender información pública?
¿Hace más fácil relacionar esa información con el territorio?
¿Permite documentar una observación ciudadana?
¿Permite contrastar una observación con evidencia existente?
¿Mejora la trazabilidad de una afirmación?
```

Si no responde ninguna, no pertenece todavía al núcleo de LADERA (ver
`Plan.md`, sección 8).

## Qué no hace el producto

- No decide una zona por el usuario: el municipio automático viene de un
  polígono DANE, nunca de una IA.
- No mezcla vistas: "Observar" nunca exige un contrato; "Preguntar" nunca
  filtra en el navegador (ver `docs/TRAZABILIDAD.md`).
- No presenta el piloto (Fase 12) ni la escala (Fase 13) como si ya
  estuvieran activados; ambos aparecen en Inicio como lectura, no como
  interruptor (`escala/puerta.py`).

## Fuente

```text
producto/recorrido.py     arma el hilo
web/app.js                 conserva zona y pregunta entre vistas
GET /api/recorrido         expone el hilo al frontend
```
