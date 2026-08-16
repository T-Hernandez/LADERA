# LADERA — `PLAN.md`

# Plan definitivo de construcción

> **Documento operativo canónico.**

>

> Este documento define el horizonte, la arquitectura de construcción, las fases,

> los entregables, los criterios de aceptación y las reglas de evolución de

> LADERA.

>

> LADERA no es únicamente un visualizador de contratos ni una plataforma de

> denuncias.

>

> Su objetivo es construir una **infraestructura de trazabilidad ciudadana**

> capaz de conectar:

>

> ```text

> INFORMACIÓN PÚBLICA

>        +

> CONTRATACIÓN

>        +

> TERRITORIO

>        +

> REPORTES CIUDADANOS

>        =

> CAPACIDAD DE OBSERVAR, CONTRASTAR E INVESTIGAR

> ```

>

> La plataforma debe permitir que una persona parta de una pregunta sobre su

> territorio y pueda avanzar progresivamente hacia la evidencia disponible:

>

> ```text

> ¿Qué se contrató aquí?

>          ↓

> ¿Cuánto dinero está relacionado?

>          ↓

> ¿Cuándo debía ejecutarse?

>          ↓

> ¿Dónde debía ocurrir?

>          ↓

> ¿Qué se ha observado o reportado en ese lugar?

>          ↓

> ¿Qué evidencia respalda cada afirmación?

>          ↓

> ¿Cómo llego a la fuente original?

> ```

>

> **Principio rector:**

>

> > LADERA no reemplaza la información pública ni declara automáticamente qué es

> > verdad. Reduce la distancia entre los datos públicos, el territorio y la

> > capacidad de la ciudadanía para contrastarlos.

---

# 0. Horizonte del proyecto

## 0.1 Objetivo final

Construir una plataforma pública de trazabilidad ciudadana que permita:

1. explorar contratos e información pública de forma comprensible;

2. visualizar su distribución territorial y temporal;

3. entender cuánto dinero está asociado a determinadas zonas, problemas o

   intervenciones;

4. identificar qué contratos están activos, finalizados, próximos a vencer o

   potencialmente relacionados con un problema territorial;

5. permitir que la ciudadanía cree reportes sobre lo que observa;

6. adjuntar evidencia, ubicación, fecha y descripción;

7. relacionar progresivamente esos reportes con contratos e información pública;

8. comparar:

   - lo contratado;

   - el dinero asociado;

   - el periodo de ejecución;

   - el territorio;

   - los reportes ciudadanos;

9. conservar una cadena de trazabilidad hacia la fuente original;

10. facilitar la investigación sin presentar hipótesis como hechos.

El horizonte no es:

```text

"encontrar corrupción automáticamente"

```

El horizonte es:

```text

hacer visible y navegable la relación entre

LO QUE SE REGISTRA PÚBLICAMENTE

                y

LO QUE LA CIUDADANÍA OBSERVA EN EL TERRITORIO

```

---

## 0.2 La unidad fundamental del producto

LADERA trabaja con cinco entidades principales:

```text

CONTRATO

    │

    │ describe una intervención, servicio,

    │ compra o actividad pública

    ▼

TERRITORIO

    │

    │ donde ocurre o debería ocurrir

    ▼

PERIODO

    │

    │ cuándo se contrató, inició, ejecutó

    │ o terminó

    ▼

REPORTE CIUDADANO

    │

    │ describe una observación

    ▼

EVIDENCIA

```

La plataforma debe permitir recorrer estas relaciones en ambas direcciones.

Ejemplo:

```text

REPORTE

"la obra sigue inconclusa"

        ↓

UBICACIÓN

Barrio / vereda / municipio

        ↓

CONTRATOS RELACIONADOS

Contrato A

Contrato B

        ↓

DATOS

valor

objeto

contratista

fecha

estado

        ↓

FUENTE ORIGINAL

registro público verificable

```

Y también:

```text

CONTRATO

        ↓

UBICACIÓN

        ↓

REPORTES RELACIONADOS

        ↓

EVIDENCIA CIUDADANA

        ↓

COMPARACIÓN TEMPORAL

```

---

# 1. Principios no negociables

## 1.1 Trazabilidad antes que espectacularidad

Todo dato relevante debe responder:

```text

¿De dónde salió?

```

Todo reporte debe responder:

```text

¿Quién o qué lo generó?

¿Cuándo?

¿Dónde?

¿Qué evidencia contiene?

¿Cuál es su estado?

```

Toda relación derivada debe responder:

```text

¿Es una relación directa,

inferida por reglas,

sugerida por IA

o todavía no verificada?

```

---

## 1.2 Separar datos, observaciones e inferencias

LADERA nunca debe mezclar estas categorías.

### Dato público

```text

"Existe un contrato registrado con valor X"

```

### Observación ciudadana

```text

"Una persona reportó que observó X"

```

### Relación

```text

"Este reporte podría estar relacionado con este contrato"

```

### Inferencia

```text

"Existen señales que justifican investigar esta relación"

```

No deben convertirse automáticamente en:

```text

"El contrato es responsable del problema"

```

---

## 1.3 Un reporte no es una verdad automáticamente

Un reporte ciudadano representa una observación o afirmación.

Por defecto:

```text

REPORTE

=

CONTENIDO GENERADO POR UN USUARIO

```

No:

```text

REPORTE

=

HECHO VERIFICADO

```

Por eso debe existir un sistema explícito de estados.

Ejemplo inicial:

```text

PUBLICADO

    ↓

EN REVISIÓN

    ↓

RELACIONADO

    ↓

VERIFICADO / DESCARTADO

```

No todos los reportes tienen que alcanzar el último estado.

---

## 1.4 La IA no puede convertirse en la fuente

La IA puede:

- buscar;

- clasificar;

- resumir;

- extraer;

- sugerir relaciones;

- explicar información compleja;

- ayudar a encontrar contratos relevantes.

La IA no puede:

- inventar contratos;

- inventar evidencia;

- inventar ubicaciones;

- declarar corrupción;

- declarar un reporte verdadero;

- ocultar incertidumbre.

Toda respuesta basada en datos debe poder volver a:

```text

FUENTE

```

---

## 1.5 La plataforma debe seguir siendo útil sin IA

La arquitectura mínima debe funcionar así:

```text

DATOS

+

FILTROS

+

BÚSQUEDA

+

MAPA

+

REPORTES

+

RELACIONES

```

La IA mejora el acceso:

```text

CONSULTA NATURAL

        ↓

IA

        ↓

INTERPRETACIÓN ESTRUCTURADA

        ↓

FILTROS / BÚSQUEDA / DATOS

```

Si el modelo falla, la plataforma sigue funcionando.

---

# 2. Arquitectura conceptual

```text

                    ┌───────────────────────┐

                    │   FUENTES PÚBLICAS    │

                    │                       │

                    │ contratos             │

                    │ entidades             │

                    │ fechas                │

                    │ valores               │

                    │ documentos            │

                    └───────────┬───────────┘

                                │

                                ▼

                    ┌───────────────────────┐

                    │   PIPELINE DE DATOS   │

                    │                       │

                    │ descarga              │

                    │ limpieza              │

                    │ clasificación         │

                    │ extracción            │

                    │ normalización         │

                    └───────────┬───────────┘

                                │

                                ▼

┌─────────────────────────────────────────────────────────┐

│                         LADERA                          │

│                                                         │

│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │

│  │ EXPLORACIÓN  │  │    MAPA      │  │   BÚSQUEDA    │ │

│  │              │  │              │  │      IA       │ │

│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘ │

│         │                 │                 │          │

│         └─────────────────┼─────────────────┘          │

│                           ▼                            │

│                    CONTRATOS Y DATOS                   │

│                           ▲                            │

│                           │                            │

│                    RELACIONES                           │

│                           │                            │

│                           ▼                            │

│                  REPORTES CIUDADANOS                   │

│                           ▲                            │

│                           │                            │

│                   FOTOS / UBICACIÓN                    │

│                   FECHA / DESCRIPCIÓN                  │

└─────────────────────────────────────────────────────────┘

```

---

# 3. Fases de construcción

La construcción sigue esta secuencia:

```text

FASE 0

Fundación y contratos del sistema

        ↓

FASE 1

Producto navegable con datos ficticios

        ↓

FASE 2

Modelo de datos y trazabilidad

        ↓

FASE 3

Ingesta de información pública

        ↓

FASE 4

Curación y normalización

        ↓

FASE 5

Resolución territorial y temporal

        ↓

FASE 6

Sistema de reportes ciudadanos

        ↓

FASE 7

Relación entre reportes y contratos

        ↓

FASE 8

Mapa de trazabilidad y comparación

        ↓

FASE 9

Búsqueda inteligente

        ↓

FASE 10

Verificación, moderación y confianza

        ↓

FASE 11

Producto integrado

        ↓

FASE 12

Piloto territorial

        ↓

FASE 13

Escalamiento

```

Regla:

> **Una fase no está terminada hasta que su salida pueda convertirse en la entrada

> exacta de la siguiente.**

---

# FASE 0 — Fundación y contratos del sistema

## Objetivo

Definir una base técnica y conceptual que permita que LADERA crezca sin que el

sistema de contratos, el mapa y los reportes terminen siendo productos separados.

## Construir

### Repositorio

```text

/apps

    /web

/services

    /api

/pipeline

    /ingestion

    /processing

    /validation

/data

    /raw

    /interim

    /final

/docs

    [PRODUCTO.md](http://PRODUCTO.md)

    MODELO_[DATOS.md](http://DATOS.md)

    [TRAZABILIDAD.md](http://TRAZABILIDAD.md)

    [MODERACION.md](http://MODERACION.md)

    [DECISIONES.md](http://DECISIONES.md)

```

### Documentos obligatorios

#### `docs/MODELO_DATOS.md`

Definir:

```text

Contrato

Reporte

Evidencia

Ubicación

Relación

Fuente

Evento temporal

```

#### `docs/TRAZABILIDAD.md`

Definir cómo representar:

```text

dato original

        ↓

transformación

        ↓

dato mostrado

```

y:

```text

reporte

        ↓

evidencia

        ↓

revisión

        ↓

relación

```

#### `docs/DECISIONES.md`

Toda decisión importante debe registrar:

```text

fecha

decisión

motivo

impacto

alternativas descartadas

```

## Salida obligatoria

```text

Repositorio ejecutable

+

Modelo de entidades definido

+

Reglas de trazabilidad definidas

+

Contratos de integración definidos

```

## Criterio de aceptación

El equipo debe poder responder sin ambigüedad:

> ¿Cómo se representa un contrato?

> ¿Cómo se representa un reporte?

> ¿Cómo sabemos qué fuente respalda un dato?

> ¿Cómo distinguimos una relación confirmada de una sugerida?

---

# FASE 1 — El producto existe antes de los datos reales

## Objetivo

Construir una primera experiencia completa utilizando datos ficticios.

El frontend no debe depender de que el pipeline real esté terminado.

## Construir

### Navegación principal

```text

EXPLORAR

MAPA

REPORTAR

BUSCAR

```

### Caso de prueba mínimo

El fixture debe incluir:

```text

Municipio A

    contratos

    dinero

    reportes

Municipio B

    contratos

    cero reportes

Municipio C

    reportes

    sin relación contractual conocida

Contrato X

    activo

Contrato Y

    finalizado

Reporte 1

    foto + ubicación

Reporte 2

    sin evidencia fotográfica

```

### Interacción

Un usuario debe poder recorrer:

```text

MAPA

→ MUNICIPIO

→ CONTRATO

→ DETALLE

→ REPORTES RELACIONADOS

```

y:

```text

MAPA

→ REPORTE

→ UBICACIÓN

→ POSIBLES CONTRATOS RELACIONADOS

```

## Criterio de aceptación

El producto debe demostrar el ciclo completo con datos ficticios.

---

# FASE 2 — Modelo real de datos y trazabilidad

## Objetivo

Implementar las entidades centrales antes de conectar fuentes reales.

## Entidad: Contrato

Campos mínimos:

```text

id

fuente

url_fuente

objeto

entidad

contratista

valor

fecha_firma

fecha_inicio

fecha_fin

estado

municipio

ubicaciones[]

texto_original

```

## Entidad: Reporte

```text

id

fecha_creacion

descripcion

categoria

estado

ubicacion

autor

evidencias[]

fecha_observacion

```

## Entidad: Evidencia

```text

id

tipo

url

metadata

fecha

```

## Entidad: Relación

Una relación nunca debe ser solamente:

```text

contrato_id

reporte_id

```

Debe incluir:

```text

id

origen

destino

tipo_relacion

metodo

confianza

estado

evidencia

creado_en

revisado_en

```

### `metodo`

```text

DIRECTA

REGLAS

IA

MANUAL

```

### `estado`

```text

SUGERIDA

CONFIRMADA

DESCARTADA

```

## Criterio de aceptación

Debe ser posible representar una relación sin fingir que tiene más certeza de la

que realmente posee.

---

# FASE 3 — Ingesta de información pública

## Objetivo

Construir un pipeline reproducible que permita descargar, conservar y reutilizar

información pública.

La primera implementación puede mantener el universo territorial y contractual

ya definido anteriormente como piloto.

## Reglas

La descarga debe:

- paginar correctamente;

- registrar errores;

- conservar una copia cruda;

- registrar fecha de actualización;

- no sobrescribir silenciosamente datos anteriores;

- permitir repetir procesamiento sin volver a descargar.

## Salidas

```text

data/raw/

    contratos_YYYY_MM_DD.csv

data/metadata/

    ingestion_manifest.json

```

## `ingestion_manifest.json`

Debe registrar:

```text

fuente

fecha

consulta

cantidad_descargada

duración

estado

hash

```

## Criterio de aceptación

Debe ser posible responder:

> ¿Qué datos exactos alimentaron esta versión de LADERA?

---

# FASE 4 — Curación y normalización

## Objetivo

Transformar los datos crudos en información utilizable sin inventar

correcciones.

## Procesos

### Identidad

Eliminar duplicados utilizando identificadores reales.

Nunca deducir identidad únicamente desde:

```text

nombre

entidad

municipio

```

### Valores

Separar:

```text

VALOR_UTILIZABLE

VALOR_NO_UTILIZABLE

VALOR_REVISAR

```

Un contrato sin valor utilizable:

```text

sigue existiendo

```

Simplemente no participa en una suma cuando corresponda.

### Estados

Normalizar fechas y estados:

```text

ACTIVO

FINALIZADO

PRÓXIMO_A_VENCER

SIN_FECHA_SUFFICIENTE

DESCONOCIDO

```

Los nombres internos pueden cambiar según la fuente, pero la lógica de producto

debe ser consistente.

## Criterio de aceptación

Cada exclusión o transformación importante debe tener un motivo rastreable.

---

# FASE 5 — Resolución territorial y temporal

## Objetivo

Convertir contratos en información navegable por territorio y periodo.

## Territorial

Resolver:

```text

departamento

municipio

corregimiento

vereda

barrio

sector

vía

otro lugar específico

```

Cuando una ubicación sea extraída del texto:

```text

ubicación

+

fragmento_literal

+

fuente

```

La IA puede participar solamente en casos ambiguos.

Nunca:

```text

IA → ubicación inventada

```

## Temporal

Cada contrato debe intentar construir:

```text

firma

inicio

fin

duración

estado actual

```

La plataforma debe poder filtrar por:

```text

año

periodo

activo

finalizado

expirado

```

## Criterio de aceptación

Un usuario debe poder responder:

> ¿Qué contratos estaban activos en este territorio durante este periodo?

---

# FASE 6 — Sistema de reportes ciudadanos

## Objetivo

Construir el segundo pilar central de LADERA.

Un reporte no es una simple publicación.

Es una unidad estructurada de observación territorial.

## Flujo

```text

CREAR REPORTE

        ↓

DESCRIBIR

        ↓

UBICAR

        ↓

FECHAR

        ↓

ADJUNTAR EVIDENCIA

        ↓

PUBLICAR / ENVIAR

        ↓

REVISIÓN

        ↓

RELACIÓN CON INFORMACIÓN PÚBLICA

```

## Campos mínimos

### Descripción

El usuario debe explicar:

```text

¿Qué observó?

```

### Categoría

Ejemplos iniciales:

```text

OBRA_INCONCLUSA

OBRA_DETERIORADA

OBRA_NO_VISIBLE

PROBLEMA_PERSISTENTE

RIESGO

OTRO

```

La taxonomía debe evolucionar mediante datos reales, no inventarse

indefinidamente desde el principio.

### Ubicación

Debe permitir:

```text

seleccionar punto

+

ajustar posición

+

municipio automático

```

### Tiempo

Separar:

```text

fecha del reporte

```

de:

```text

fecha en que ocurrió la observación

```

### Evidencia

Permitir inicialmente:

```text

fotografía

```

La evidencia debe almacenarse separada del texto.

## Criterio de aceptación

Una persona debe poder crear un reporte completo sin necesitar conocer ningún

contrato.

---

# FASE 7 — Relación entre reportes y contratos

## Objetivo

Construir el mecanismo que convierte a LADERA en una plataforma de contraste.

## Tipos de relación

```text

RELACIÓN_DIRECTA

```

Existe una conexión explícita.

Ejemplo:

```text

el usuario identifica el contrato

```

---

```text

RELACIÓN_TERRITORIAL

```

El contrato y el reporte coinciden territorialmente.

---

```text

RELACIÓN_TEMPORAL

```

Las fechas son compatibles.

---

```text

RELACIÓN_SEMÁNTICA

```

El contenido del contrato y el reporte parecen describir una intervención o

problema relacionado.

---

```text

RELACIÓN_COMPUESTA

```

La relación utiliza más de una señal.

## Motor inicial

La primera versión no necesita IA.

```text

score =

territorio

+

tiempo

+

categoría

+

similitud básica

```

Después:

```text

CASOS AMBIGUOS

        ↓

IA

        ↓

SUGERENCIA ESTRUCTURADA

        ↓

RELACIÓN_SUGERIDA

```

La IA nunca crea automáticamente una relación confirmada.

## Criterio de aceptación

La interfaz debe mostrar claramente:

```text

RELACIÓN CONFIRMADA

```

versus:

```text

POSIBLE RELACIÓN

```

---

# FASE 8 — Mapa de trazabilidad

## Objetivo

Convertir el mapa en el lugar donde las distintas capas de información pueden

contrastarse.

## Capas iniciales

```text

CONTRATOS

REPORTES

DINERO

ESTADO CONTRACTUAL

PERIODO

```

## Ejemplo conceptual

Un usuario selecciona una zona:

```text

────────────────────────

Municipio X

$ 2.400 millones

12 contratos

5 finalizados

3 activos

8 reportes ciudadanos

2 contratos relacionados

3 relaciones sugeridas

────────────────────────

```

El usuario debe poder activar y desactivar capas.

## Comparación temporal

El mapa debe permitir:

```text

2024

2025

2026

```

y observar:

```text

contratación

versus

reportes

```

No para demostrar causalidad automáticamente.

Sí para permitir encontrar:

```text

patrones

concentraciones

persistencias

contrastes

```

## Criterio de aceptación

Debe ser posible identificar una zona y entender rápidamente:

> qué información pública existe, cuánto dinero está asociado y qué está siendo

> reportado allí.

---

# FASE 9 — Búsqueda inteligente

## Objetivo

Eliminar la necesidad de que el ciudadano conozca exactamente cómo están

estructurados los datos públicos.

## Ejemplos

```text

"Muéstrame contratos que terminaron el año pasado

y tienen reportes de obras inconclusas"

```

```text

"¿Qué contratos hay relacionados con esta zona?"

```

```text

"Obras de mitigación de riesgo que siguen teniendo

reportes ciudadanos"

```

## Arquitectura

```text

PREGUNTA

    ↓

INTERPRETACIÓN

    ↓

CONSULTA ESTRUCTURADA

    ↓

FILTROS

    ↓

DATOS

    ↓

RESULTADOS

    ↓

FUENTES

```

La IA debe producir una estructura verificable.

Ejemplo:

```json

{

  "territorio": "X",

  "estado_contrato": "FINALIZADO",

  "categoria_reporte": "OBRA_INCONCLUSA",

  "periodo": {

    "desde": "2025-01-01"

  }

}

```

El backend ejecuta la consulta.

No:

```text

IA responde directamente basándose en su memoria.

```

## Criterio de aceptación

Toda respuesta de búsqueda debe permitir inspeccionar:

```text

qué contratos

qué reportes

qué filtros

qué fuentes

```

produjeron el resultado.

---

# FASE 10 — Moderación, verificación y confianza

## Objetivo

Evitar que el sistema de reportes destruya la credibilidad de la plataforma.

## Estados

```text

BORRADOR

PUBLICADO

EN_REVISIÓN

RELACIONADO

VERIFICADO

DESCARTADO

RETIRADO

```

## Moderación

Implementar:

- detección de contenido inválido;

- protección contra spam;

- límites de frecuencia;

- reporte de contenido;

- revisión administrativa;

- registro de decisiones.

## Auditoría

Toda acción sensible debe producir:

```text

actor

acción

fecha

objeto

resultado

```

## Criterio de aceptación

Debe ser posible explicar:

> ¿Por qué este reporte tiene este estado?

---

# FASE 11 — Producto integrado

## Objetivo

Unificar contratos, mapa, reportes y búsqueda en una sola experiencia.

## Recorrido principal

```text

1. Usuario detecta un problema

        ↓

2. Busca la zona

        ↓

3. Observa contratos relacionados

        ↓

4. Consulta periodos y valores

        ↓

5. Revisa reportes existentes

        ↓

6. Agrega nueva evidencia

        ↓

7. La plataforma actualiza las relaciones

        ↓

8. Otros usuarios pueden continuar investigando

```

## Criterio de aceptación

LADERA debe sentirse como un único producto.

No como:

```text

mapa

+

buscador

+

foro

```

pegados artificialmente.

---

# FASE 12 — Piloto territorial

## Objetivo

Validar si la trazabilidad funciona con personas reales antes de escalar.

## Alcance inicial

Mantener un territorio y universo de datos suficientemente delimitado para

poder garantizar calidad.

La primera implementación puede conservar el piloto territorial previamente

definido mientras se valida el nuevo modelo.

## Medir

```text

reportes creados

reportes útiles

reportes duplicados

relaciones sugeridas

relaciones confirmadas

contratos consultados

búsquedas realizadas

tiempo hasta encontrar información

```

La métrica más importante no es:

```text

número de usuarios

```

sino:

```text

¿La plataforma permitió descubrir o contrastar información

que antes era difícil de relacionar?

```

---

# FASE 13 — Escalamiento

## Objetivo

Convertir el piloto en una infraestructura extensible.

## Escalar

### Territorialmente

```text

municipio

→ departamento

→ región

→ país

```

### Por fuentes

```text

contratación

→ documentos

→ presupuestos

→ otras fuentes públicas

```

### Por comunidad

```text

usuarios

→ organizaciones

→ periodistas

→ investigadores

→ comunidades locales

```

## Regla de escalamiento

Nunca escalar únicamente porque técnicamente es posible.

Primero demostrar:

```text

calidad

+

utilidad

+

trazabilidad

+

capacidad de moderación

```

---

# 4. Arquitectura de datos objetivo

```text

                    FUENTES

                       │

                       ▼

                 RAW DATA LAYER

                       │

                       ▼

                NORMALIZATION LAYER

                       │

                       ▼

                  CORE ENTITIES

             ┌─────────┼─────────┐

             ▼         ▼         ▼

         CONTRATOS  TERRITORIO  TIEMPO

             │         │         │

             └─────────┼─────────┘

                       ▼

                  RELACIONES

                       ▲

                       │

                    REPORTES

                       │

                       ▼

                   EVIDENCIA

                       │

                       ▼

                 PRODUCT LAYER

             ┌─────────┼─────────┐

             ▼         ▼         ▼

            MAPA    EXPLORAR   BUSCAR

```

---

# 5. Reglas de implementación

## 5.1 Ninguna transformación destruye su entrada

```text

raw

    ↓

interim

    ↓

normalized

    ↓

final

```

Nunca:

```text

sobrescribir raw

```

---

## 5.2 Toda relación tiene procedencia

```text

relation.method

```

es obligatorio.

Ejemplo:

```text

MANUAL

RULE_BASED

AI_ASSISTED

USER_DECLARED

```

---

## 5.3 La confianza no puede ocultarse

Una relación sugerida por IA debe poder mostrar:

```text

por qué fue sugerida

```

No únicamente:

```text

92% de confianza

```

El usuario debe ver señales concretas:

```text

misma ubicación

+

periodos compatibles

+

descripción relacionada

```

---

## 5.4 La evidencia debe sobrevivir al producto

La estructura interna debe permitir volver desde cualquier elemento visible hacia:

```text

registro

fuente

fragmento

archivo

reporte

evidencia

```

---

# 6. Definición de terminado

LADERA alcanza su primer horizonte completo cuando:

## Información pública

- [ ] existe una fuente pública integrada de forma reproducible;

- [ ] los datos tienen procedencia;

- [ ] contratos pueden explorarse individualmente;

- [ ] los valores y fechas son rastreables;

- [ ] las ubicaciones tienen evidencia cuando fueron extraídas;

- [ ] los estados temporales son comprensibles.

## Reportes

- [ ] un usuario puede crear un reporte;

- [ ] puede adjuntar evidencia;

- [ ] puede seleccionar una ubicación;

- [ ] puede indicar cuándo observó el problema;

- [ ] los reportes tienen estados;

- [ ] existe moderación básica.

## Relaciones

- [ ] un reporte puede relacionarse con contratos;

- [ ] las relaciones tienen método;

- [ ] las relaciones pueden confirmarse o descartarse;

- [ ] las sugerencias no se presentan como hechos.

## Mapa

- [ ] muestra contratos;

- [ ] muestra reportes;

- [ ] permite filtrar por periodo;

- [ ] permite explorar una zona;

- [ ] permite contrastar capas.

## Búsqueda

- [ ] existe búsqueda estructurada;

- [ ] existe búsqueda asistida por lenguaje natural;

- [ ] la IA genera consultas, no verdades;

- [ ] los resultados muestran fuentes.

## Confianza

- [ ] toda decisión sensible queda auditada;

- [ ] la plataforma diferencia claramente:

  - datos públicos;

  - reportes ciudadanos;

  - relaciones sugeridas;

  - relaciones verificadas;

- [ ] ninguna afirmación crítica depende únicamente de una salida de IA.

---

# 7. Orden de prioridades

## PRIORIDAD 1 — El núcleo

```text

CONTRATOS

+

MAPA

+

REPORTES

```

Sin esto no existe LADERA.

---

## PRIORIDAD 2 — El contraste

```text

RELACIONES

+

TIEMPO

+

TERRITORIO

```

Aquí empieza a aparecer el verdadero valor diferencial.

---

## PRIORIDAD 3 — Accesibilidad

```text

BÚSQUEDA INTELIGENTE

+

EXPLICACIONES

+

RESÚMENES

```

Aquí la IA ayuda a democratizar el acceso.

---

## PRIORIDAD 4 — Confianza

```text

MODERACIÓN

+

VERIFICACIÓN

+

AUDITORÍA

+

TRANSPARENCIA

```

Esto determina si el proyecto puede sobrevivir al uso real.

---

## PRIORIDAD 5 — Escalamiento

```text

MÁS TERRITORIOS

MÁS FUENTES

MÁS USUARIOS

```

Nunca antes de validar el núcleo.

---

# 8. Regla de producto

Cada nueva feature debe responder al menos una de estas preguntas:

```text

¿Hace más fácil entender información pública?

```

```text

¿Hace más fácil relacionar esa información con el territorio?

```

```text

¿Permite documentar una observación ciudadana?

```

```text

¿Permite contrastar una observación con evidencia existente?

```

```text

¿Mejora la trazabilidad de una afirmación?

```

Si no responde ninguna, no pertenece todavía al núcleo de LADERA.

---

# 9. Horizonte final

El horizonte de LADERA es construir algo que permita este ciclo:

```text

EL ESTADO PUBLICA INFORMACIÓN

            ↓

LADERA LA ESTRUCTURA

            ↓

LA CIUDADANÍA LA ENTIENDE

            ↓

LA CIUDADANÍA OBSERVA EL TERRITORIO

            ↓

CREA REPORTES Y APORTA EVIDENCIA

            ↓

LADERA RELACIONA LAS CAPAS

            ↓

SURGEN CONTRASTES Y PREGUNTAS

            ↓

LAS PERSONAS PUEDEN INVESTIGAR

            ↓

LA INFORMACIÓN SIGUE SIENDO VERIFICABLE

```

El producto terminado no pretende decirle a la ciudadanía:

> "Esto es corrupción."

Pretende darle las herramientas para preguntar:

> **"Aquí hay un contrato, este era su objetivo, este era su periodo, este es el

> dinero asociado y esto es lo que las personas están observando en el

> territorio. Ahora puedo seguir la evidencia."**

---

# 10. Definición final de LADERA

> **LADERA es una plataforma de trazabilidad ciudadana que conecta información

> pública, contratación estatal, territorio y reportes ciudadanos para hacer

> visible la relación entre lo que se registra, lo que se promete y lo que las

> personas observan.**

>

> No reemplaza a las fuentes oficiales.

>

> No convierte automáticamente un reporte en verdad.

>

> No convierte una correlación en una acusación.

>

> **Hace algo distinto: crea una superficie común donde la información pública y

> la experiencia del territorio pueden encontrarse, contrastarse y seguirse hasta

> su evidencia.**