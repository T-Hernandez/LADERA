Sí. Voy a hacerlo como **el documento operativo definitivo**, no como otro resumen de la especificación: la especificación define *qué es LADERA*; `PLAN.md` define **en qué orden se construye, qué artefacto debe existir al terminar cada fase, quién es responsable, qué se valida y cuándo se corta una línea de trabajo**. Respeto las decisiones ya congeladas: Antioquia y sus 125 municipios, SECOP II como fuente única, pipeline por archivos, extracción verificable mediante fragmento literal y degradación funcional si falla la IA.  

# LADERA — `PLAN.md`

````md
# LADERA — Plan definitivo de construcción

> **Documento operativo canónico.**
>
> Este documento define cómo se construye, integra, verifica y presenta
> LADERA. No redefine el producto. Las decisiones de producto, alcance,
> metodología y arquitectura viven en la especificación canónica.
>
> Si este plan entra en conflicto con una decisión explícitamente congelada
> en la especificación, prevalece la especificación.
>
> **Principio rector:** primero un producto verdadero que funcione; después,
> todo lo demás.

---

# 0. Horizonte del proyecto

## 0.1 Objetivo final

Construir una herramienta pública que permita recorrer los **125 municipios de
Antioquia** y consultar, sobre un conjunto definido de contratos publicados en
SECOP II:

- cuántos contratos de gestión del riesgo fueron identificados;
- cuánto dinero puede sumarse con cifras utilizables;
- qué municipios no registran contratación identificada dentro del conjunto;
- qué municipios tienen contratos que citan una declaratoria de calamidad o
  urgencia manifiesta;
- dónde se localiza una obra por debajo del nivel municipal cuando esa
  información aparece literalmente en el objeto contractual;
- qué fragmento del contrato respalda cada ubicación mostrada;
- cómo llegar al registro original para verificarlo;
- qué contratos del conjunto analizado responden a una pregunta
  formulada en lenguaje cotidiano, sin exigir jerga de contratación
  pública.

LADERA no demuestra corrupción, ausencia absoluta de inversión ni ejecución
real de una obra. Produce señales verificables y puntos de partida para
investigar.

---

## 0.2 Definición de "terminado"

LADERA se considera terminada para el horizonte actual cuando se cumplen
simultáneamente estas condiciones:

### Datos

- [ ] Existe una descarga completa y cacheada del universo definido.
- [ ] Cada etapa del pipeline puede ejecutarse de forma independiente.
- [ ] Ninguna etapa sobrescribe su entrada.
- [ ] Los 125 municipios existen en `datos.json`.
- [ ] Los conteos y sumas cumplen los invariantes definidos.
- [ ] Los contratos sin valor utilizable siguen contando como contratos.
- [ ] Los valores excluidos tienen un motivo registrado.
- [ ] La cobertura municipal se calcula sobre los 125 municipios.
- [ ] Toda ubicación submunicipal visible tiene un fragmento literal
      verificado contra el texto original.

### Producto

- [ ] El mapa funciona sin depender de una capa base externa.
- [ ] Un usuario puede hacer clic en cualquier municipio.
- [ ] Los tres estados de municipio son distinguibles.
- [ ] La ficha muestra contratos, monto cuando existe, calamidad y lugares.
- [ ] Cada lugar permite llegar a la fuente original.
- [ ] Las limitaciones metodológicas están visibles.
- [ ] Ningún texto en pantalla afirma más de lo que los datos permiten.
- [ ] Existe una búsqueda sobre el conjunto analizado: por palabras
      clave si la IA no está disponible, y por pregunta en lenguaje
      cotidiano cuando sí lo está.
- [ ] Cada resultado de búsqueda apunta a un contrato ya curado y a
      su fuente original.

### Demostración

- [ ] Los casos mostrados fueron seleccionados después de construir el conjunto.
- [ ] Cada dato usado en la demo fue verificado contra SECOP.
- [ ] Existe al menos un caso que contradice o matiza la hipótesis.
- [ ] Existe un caso que demuestre claramente la extracción verificable.
- [ ] La aplicación puede demostrarse aunque falle la IA.
- [ ] Existe una copia o recorrido de respaldo para la presentación.

---

# 1. Reglas no negociables

Estas reglas existen para evitar repetir errores ya identificados.

## 1.1 No se vuelve a diseñar mientras se construye

Las siguientes decisiones están cerradas:

- territorio: Antioquia;
- cobertura: 125 municipios;
- fuente principal: SECOP II;
- universo inicial: contratos de obra desde 2019;
- arquitectura: archivos intermedios, no base de datos;
- frontend: HTML + CSS + JavaScript;
- mapa: Leaflet + GeoJSON local;
- intercambio datos/frontend: `web/assets/datos.json`;
- IA: solo donde las reglas determinísticas no bastan;
- búsqueda: recorre únicamente el conjunto ya curado; no descarga,
  no inventa contratos y no consulta fuentes externas;
- ubicación submunicipal: únicamente con fragmento literal verificable;
- ausencia: "sin contratación identificada en los contratos analizados",
  nunca "sin inversión";
- calamidad: señal encontrada en el texto contractual, no registro completo
  de emergencias;
- LADERA se detiene en el nivel de indicio.

Cualquier nueva idea se registra en `docs/DECISIONES.md` como **posterior al
MVP**. No interrumpe la construcción.

---

## 1.2 Nada existe hasta que puede inspeccionarse

Una función no está terminada porque el código "parezca correcto".

Cada fase debe producir uno de estos artefactos:

1. archivo;
2. reporte;
3. pantalla;
4. prueba reproducible;
5. caso verificable.

Si no deja un artefacto inspeccionable, la fase no está terminada.

---

## 1.3 Nunca se vuelve a descargar para corregir lógica

La red pertenece exclusivamente a `p1_bajar.py`.

Una vez descargado el crudo:

```text
SECOP II → contratos_crudos.csv
````

todo ajuste posterior ocurre localmente.

Cambiar palabras clave no requiere descargar.
Cambiar reglas de municipio no requiere descargar.
Cambiar umbrales no requiere descargar.
Cambiar el prompt no requiere descargar.

---

## 1.4 Contar y sumar son operaciones diferentes

La presencia de un contrato y la disponibilidad de una cifra son variables
distintas.

```text
contratos            = todos los contratos válidos
contratos_con_cifra  = contratos con valor utilizable
plata_total          = suma de contratos_con_cifra
```

Un contrato válido con valor `0`, vacío o no utilizable:

* sigue existiendo;
* sigue contando;
* no suma dinero.

---

## 1.5 La IA no es una fuente

El modelo:

* no inventa municipios;
* no calcula totales;
* no corrige valores;
* no decide qué cifras son verdaderas;
* no concluye irregularidades;
* no aporta conocimiento externo.

Solo puede estructurar información que ya existe en el texto.

En la búsqueda ocurre lo mismo: el modelo puede traducir una pregunta
cotidiana a filtros o términos, y puede señalar por qué un contrato
ya existente parece pertinente. No puede:

* inventar un contrato que no esté en `datos.json`;
* afirmar que "no hay inversión" porque la búsqueda no halló nada;
* concluir irregularidad, abandono o corrupción;
* ampliar el universo más allá de los contratos analizados.

Toda coincidencia mostrada debe sobrevivir esta prueba:

```text
el resultado ∈ conjunto curado
AND el fragmento que justifica la coincidencia ∈ texto original
```

Si falla, se descarta.

Toda extracción de ubicación debe sobrevivir esta prueba:

```text
fragmento devuelto ∈ objeto contractual original
```

Si falla, se descarta.

---

# 2. Estructura definitiva del repositorio

```text
ladera/
│
├── PLAN.md
├── README.md
├── requirements.txt
├── config.py
│
├── pipeline/
│   ├── __init__.py
│   ├── comun.py
│   ├── p1_bajar.py
│   ├── p2_filtrar.py
│   ├── p3_curar.py
│   ├── p4_ia.py
│   └── p5_json.py
│
├── data/
│   ├── raw/
│   │   └── contratos_crudos.csv
│   │
│   ├── interim/
│   │   ├── p2_filtrado.csv
│   │   ├── p3_limpio.csv
│   │   ├── p3_revisar_a_mano.csv
│   │   └── p3_excluidos.csv
│   │
│   └── final/
│       └── reporte.txt
│
├── web/
│   ├── index.html
│   ├── estilos.css
│   ├── app.js
│   ├── servidor.py
│   │
│   └── assets/
│       ├── municipios_antioquia.geojson
│       ├── municipios_lookup.json
│       └── datos.json
│
└── docs/
    ├── CONTRATO.md
    └── DECISIONES.md
```

## 2.1 Propiedad de cada zona

| Zona                 | Responsable principal | Regla                                                       |
| -------------------- | --------------------- | ----------------------------------------------------------- |
| `config.py`          | Datos                 | Todo parámetro ajustable vive aquí                          |
| `pipeline/`          | Datos                 | Cada etapa es independiente                                 |
| `data/`              | Datos                 | Nunca editar resultados manualmente sin registrar el cambio |
| `web/`               | Frontend              | Consume únicamente artefactos definidos                     |
| `docs/CONTRATO.md`   | Datos + Frontend      | Se congela antes de integrar                                |
| `docs/DECISIONES.md` | Calidad/producto      | Toda desviación queda registrada                            |

---

# 3. Fases de construcción

La construcción sigue esta secuencia:

```text
FASE 0
Cimientos
    ↓
FASE 1
Interfaz con datos ficticios
    ↓
FASE 2
Descarga real
    ↓
FASE 3
Filtrado y cobertura
    ↓
FASE 4
Curación y calidad
    ↓
FASE 5
Extracción verificable
    ↓
FASE 6
Contrato de integración
    ↓
FASE 7
Datos reales en pantalla
    ↓
FASE 7B
Búsqueda asistida
    ↓
FASE 8
Verificación independiente
    ↓
FASE 9
Demo y congelación
```

La regla es:

> **Una fase no se considera terminada hasta que su salida pueda convertirse en
> la entrada exacta de la siguiente.**

---

# FASE 0 — Cimientos

## Objetivo

Crear un entorno donde el equipo pueda trabajar en paralelo sin bloquearse.

## Entrada

* especificación canónica;
* GeoJSON validado;
* diccionario de municipios validado.

## Tareas

### Repositorio

* [ ] Crear repositorio.
* [ ] Crear estructura de carpetas.
* [ ] Crear `.gitignore`.
* [ ] Crear `requirements.txt`.
* [ ] Crear `README.md` mínimo con instrucciones de ejecución.

### Configuración

* [ ] Crear `config.py`.
* [ ] Centralizar rutas.
* [ ] Centralizar umbrales.
* [ ] Centralizar vocabularios.
* [ ] Centralizar parámetros de API y modelo.
* [ ] Leer secretos desde variables de entorno.

### Utilidades

Crear `pipeline/comun.py` con:

* `norm()`;
* normalización de texto;
* lectura segura de CSV;
* escritura consistente;
* logging;
* funciones compartidas.

### Contrato de integración

Crear `docs/CONTRATO.md` antes de que exista el dato real.

Debe definir:

* claves de primer nivel;
* campos de `resumen`;
* campos de municipio;
* campos de lugar;
* tipos;
* valores `null`;
* invariantes.

### Frontend

* [ ] Levantar servidor Flask.
* [ ] Servir `index.html`.
* [ ] Cargar GeoJSON.
* [ ] Crear `datos.json` ficticio con al menos cinco municipios.

## Salida obligatoria

```text
Repositorio ejecutable
+
Servidor local funcionando
+
GeoJSON visible
+
datos.json ficticio válido
+
CONTRATO.md congelado
```

## Criterio de aceptación

Una persona del equipo debe poder clonar el repositorio, instalar
dependencias y ver el mapa sin ejecutar el pipeline.

---

# FASE 1 — El producto existe antes de los datos reales

## Objetivo

Terminar la estructura completa de interacción usando datos ficticios.

El frontend no espera al pipeline.

## Construir

### Mapa

* cargar `municipios_antioquia.geojson`;
* ejecutar `fitBounds`;
* eliminar dependencia de tiles externos;
* implementar hover;
* implementar clic;
* resaltar municipio seleccionado.

### Estados visuales

Todo municipio debe representar uno de tres estados:

#### Estado A — Sin contratación identificada

```text
contratos == 0
```

Representación:

* trama diagonal;
* texto metodológicamente preciso.

#### Estado B — Contratos sin cifra utilizable

```text
contratos > 0
AND contratos_con_cifra == 0
```

Representación distinta al estado A.

#### Estado C — Contratos con cifra

```text
contratos_con_cifra > 0
```

Representación:

* escala de relleno proporcional al dinero contratado.

### Calamidad

`fue_calamidad` utiliza un segundo canal visual:

```text
dinero     → relleno
calamidad  → borde
```

Nunca mezclar ambos conceptos en un único color.

### Panel

Construir:

1. identidad;
2. resumen;
3. ficha de municipio;
4. lista de lugares;
5. limitaciones;
6. caja de búsqueda sobre el conjunto analizado, usable con
   palabras clave aunque la IA no esté disponible.

## Datos ficticios mínimos

El fixture debe contener deliberadamente:

* un municipio sin contratos;
* uno con contratos pero sin cifra;
* uno con dinero;
* uno con calamidad;
* uno con una ubicación verificable ficticia.

No crear fixtures que solo prueben el caso feliz.

## Salida obligatoria

```text
Mapa navegable
+
Ficha funcional
+
Tres estados visibles
+
Calamidad visible
+
Lista de lugares
+
Búsqueda por palabras clave sobre el fixture
```

## Criterio de aceptación

El frontend debe poder cambiar de datos ficticios a reales sin modificar su
lógica.

La única operación permitida al integrar es reemplazar:

```text
web/assets/datos.json
```

---

# FASE 2 — Ingesta real

## Objetivo

Descargar una copia completa, estable y reutilizable del universo inicial.

## Implementar `p1_bajar.py`

Consulta inicial:

```text
departamento = Antioquia
tipo_de_contrato = Obra
fecha_de_firma > 2019-01-01
```

Seleccionar únicamente las columnas necesarias.

La consulta debe:

* usar igualdad, no búsquedas con comodines iniciales;
* usar `$order=:id`;
* paginar con `$limit` y `$offset`;
* registrar progreso;
* detenerse visiblemente ante un fallo;
* guardar el resultado únicamente al completar una descarga válida.

## Prohibido

* ignorar timeouts;
* continuar después de respuestas corruptas;
* reportar cobertura parcial como completa;
* descargar de nuevo para corregir una fase posterior.

## Validaciones al terminar

* [ ] Archivo no vacío.
* [ ] Columnas esperadas presentes.
* [ ] `id_contrato` presente.
* [ ] No hay error HTTP silencioso.
* [ ] Se registra número total descargado.
* [ ] Se registra duración.

## Salida

```text
data/raw/contratos_crudos.csv
```

## Punto de decisión

Si la consulta inicial resulta insuficiente para la cobertura mínima esperada,
no se modifica el frontend.

Se abre una segunda pasada controlada con los tipos de contrato definidos en
la especificación.

---

# FASE 3 — Filtrado temático y resolución territorial

## Objetivo

Transformar el universo crudo en un subconjunto relevante y asignable a los
municipios.

## Implementar `p2_filtrar.py`

El procesamiento es completamente local.

## Paso 1 — Normalización

Aplicar normalización consistente sobre:

* objeto contractual;
* descripción;
* ciudad;
* nombres municipales.

## Paso 2 — Inclusión temática

Buscar vocabulario asociado con:

* contención;
* estabilidad;
* movimientos en masa;
* erosión;
* inundación;
* drenaje;
* mitigación;
* gestión del riesgo;
* calamidad;
* protección territorial.

## Paso 3 — Exclusión por ruido

Eliminar coincidencias temáticas conocidas que correspondan a:

* riesgos laborales;
* salud;
* seguridad vial;
* fauna;
* programas sociales;
* otros falsos positivos registrados.

## Paso 4 — Resolver municipio

Orden de prioridad:

```text
1. Municipio mencionado en objeto contractual.
2. Ciudad de la entidad como respaldo.
```

Reglas:

* buscar nombres de mayor longitud antes que nombres cortos;
* normalizar mediante `norm()`;
* aplicar alias;
* marcar contratos multimunicipio;
* no repartir artificialmente el valor entre municipios.

## Paso 5 — Medir cobertura

Calcular:

```text
municipios_con_contratos
municipios_sin_contratos
cobertura = municipios_con_contratos / 125
```

## Salida

```text
data/interim/p2_filtrado.csv
```

## Reportar

```text
Contratos crudos:               N
Contratos tras filtro temático: N
Municipios resueltos:           N / 125
Municipios sin resolver:        N
Multimunicipio:                 N
```

## Punto de decisión

Si la cobertura es menor al umbral definido:

1. revisar vocabulario;
2. ajustar únicamente `config.py`;
3. volver a ejecutar `p2_filtrar.py`.

No volver a descargar.

---

# FASE 4 — Curación y calidad de datos

## Objetivo

Separar registros utilizables, revisables y excluidos sin inventar
correcciones.

## Implementar `p3_curar.py`

### Paso 1 — Eliminar duplicados correctamente

La identidad es:

```text
id_contrato
```

Nunca:

```text
nombre_entidad
```

### Paso 2 — Validar estructura

Revisar:

* objeto contractual;
* fecha;
* municipio;
* identificador;
* texto mínimo.

### Paso 3 — Clasificar valores

Usar los umbrales definidos en `config.py`.

Nunca reemplazar un valor absurdo por una estimación.

Un registro puede ser:

```text
LIMPIO
REVISAR_A_MANO
EXCLUIDO
```

### Paso 4 — Detectar contradicción interna

Comparar el valor contractual contra otros valores presentes en el mismo
registro.

La lógica debe buscar contradicciones aritméticas evidentes, no aplicar
simplemente un límite estadístico.

### Paso 5 — Preservar contratos sin cifra

Un contrato válido sin valor utilizable permanece en `p3_limpio.csv`.

Solo queda fuera de la suma.

## Salidas

```text
data/interim/p3_limpio.csv
data/interim/p3_revisar_a_mano.csv
data/interim/p3_excluidos.csv
data/final/reporte.txt
```

## Revisión manual

Los contratos en revisión se inspeccionan individualmente.

Para cada decisión:

```text
id_contrato
decisión
motivo
persona que revisó
fecha
```

No editar directamente el CSV sin dejar trazabilidad.

## Criterio de aceptación

Debe ser posible responder:

> ¿Por qué este contrato no aparece en la suma?

buscando su identificador y encontrando un destino o motivo.

---

# FASE 5 — Clasificación y extracción verificable

## Objetivo

Identificar qué contratos representan intervención física y extraer ubicaciones
submunicipales cuando el texto realmente las contiene.

---

## 5.1 Clasificación de intervención física

Pregunta:

> ¿Este contrato describe una intervención física en el territorio destinada a
> reducir riesgo de desastre?

### Resolución barata

```text
NO_SEGURO → descartar sin modelo
SI_SEGURO → aceptar sin modelo
AMBIGUO   → enviar al modelo
```

El modelo solo recibe casos ambiguos.

---

## 5.2 Selección para extracción

Solo analizar contratos que:

```text
es_obra_fisica == true
```

y que además tengan alguna pista de ubicación.

Ejemplos:

```text
barrio
vereda
quebrada
corregimiento
sector
calle
carrera
puente
vía
loma
cerro
```

No pagar por pedir una ubicación donde el texto no ofrece ninguna pista.

---

## 5.3 Prompt

El prompt debe imponer estas reglas:

1. `ninguno` es una respuesta válida.
2. No inferir información.
3. No completar nombres con conocimiento externo.
4. Devolver solo información literalmente presente.
5. El municipio por sí solo no cuenta como ubicación submunicipal.
6. Devolver el fragmento literal exacto que justifica la respuesta.

La respuesta debe ser estructurada.

---

## 5.4 Verificación obligatoria

Después de recibir la respuesta:

```text
normalizar(fragmento)
    ↓
buscar en objeto original
    ↓
¿existe?
    ├── sí → aceptar
    └── no → descartar
```

Nunca mostrar una ubicación únicamente porque el modelo la afirmó.

---

## 5.5 Medición

Registrar:

```text
consultados
respuestas_con_lugar
ubicaciones_aceptadas
ubicaciones_descartadas
tasa_de_alucinacion
```

Definición:

```text
ubicaciones_descartadas_por_fragmento_inexistente
/
respuestas_en_que_el_modelo_afirmó_un_lugar
```

---

## 5.6 Punto de decisión

Si la tasa supera el umbral definido:

1. ajustar el prompt una vez;
2. volver a ejecutar la extracción;
3. medir de nuevo.

Si persiste:

```text
DESACTIVAR EXTRACCIÓN SUBMUNICIPAL
```

El producto continúa funcionando a nivel municipal.

No se improvisa un método menos verificable.

---

# FASE 6 — Generación del contrato de datos

## Objetivo

Convertir el resultado del pipeline en el único archivo que necesita el
frontend.

## Implementar `p5_json.py`

Generar:

```text
web/assets/datos.json
```

Estructura:

```json
{
  "resumen": {},
  "municipios": {}
}
```

## Reglas

### Los 125 municipios siempre existen

Incluso:

```json
{
  "contratos": 0,
  "contratos_con_cifra": 0,
  "plata_total": 0,
  "lugares": []
}
```

La ausencia se representa con cero, no con una clave inexistente.

### Lugares

Cada lugar debe tener:

* nombre;
* fragmento;
* valor o `null`;
* año;
* vehículo;
* calamidad;
* URL.

### Orden

Los lugares se ordenan por valor descendente cuando existe.

Se limita la cantidad mostrada según el contrato definido.

---

## Validación automática

Antes de escribir el archivo final:

```text
[ ] resumen.municipios_con_contratos +
    resumen.municipios_sin_contratos == 125

[ ] existen exactamente 125 claves municipales

[ ] contratos_con_cifra <= contratos

[ ] plata_total >= 0

[ ] ningún lugar carece de fragmento

[ ] ningún lugar tiene fragmento no verificable

[ ] cada municipio tiene nombre y código DANE
```

Si una validación falla:

```text
NO GENERAR datos.json FINAL
```

---

# FASE 7 — Integración

## Objetivo

Demostrar que el contrato entre pipeline y frontend realmente funciona.

## Procedimiento

1. Ejecutar pipeline.
2. Generar `datos.json`.
3. Levantar servidor.
4. Abrir aplicación.
5. Recorrer los 125 municipios.
6. Comparar una muestra contra el JSON.
7. Comparar una muestra contra los CSV.
8. Verificar que la interfaz no recalcula datos que pertenecen al pipeline.

## Regla

El frontend:

* puede formatear;
* puede ordenar visualmente;
* puede seleccionar;
* puede filtrar interacción.

El frontend no debe:

* recalcular el municipio;
* reinterpretar valores;
* inventar estados;
* inferir calamidad;
* modificar agregados.

---

# FASE 7B — Búsqueda asistida de contratos

## Objetivo

Permitir que una persona sin jerga de contratación pública encuentre,
dentro del conjunto ya analizado, los contratos que responden a una
pregunta cotidiana.

La búsqueda no amplía LADERA. Hace legible el mismo universo que el
mapa ya muestra.

Preguntas que debe poder recibir:

```text
¿Hay obras de contención en Medellín?
¿Qué contratos mencionan una quebrada?
¿Dónde se citó urgencia manifiesta?
muros de contención después de 2022
```

La persona no necesita saber cómo se llama un campo en SECOP II.

## Por qué existe

SECOP II es público, pero en la práctica es opaco: hay que conocer
filtros, vocabularios y códigos. LADERA ya curó un subconjunto
verificable. La búsqueda es el puente entre esa curaduría y una
pregunta formulada como la haría un vecino, un periodista o un
concejal.

No es un chatbot. No investiga por la persona. Devuelve contratos
ya existentes y el camino de vuelta a la fuente.

## Arquitectura

Dos capas. La segunda puede apagarse.

```text
pregunta de la persona
    ↓
1. BÚSQUEDA DETERMINÍSTICA  (siempre)
   palabras clave, municipio, año, calamidad, objeto
    ↓
2. INTERPRETACIÓN CON IA    (opcional)
   traduce la pregunta a filtros y términos
   sobre el mismo conjunto
    ↓
resultados ⊆ datos.json
    ↓
cada resultado muestra:
   municipio + fragmento literal + enlace a SECOP
```

La red de SECOP no se toca. No se vuelve a descargar. No se consulta
nada que no esté ya en `datos.json` o en los CSV curados.

## Implementar

### Interfaz

En el panel, no como una pantalla aparte:

* un campo de pregunta;
* ejemplos visibles de preguntas válidas;
* lista de resultados con municipio, año, monto si existe y
  fragmento que justifica la coincidencia;
* clic en un resultado = seleccionar ese municipio en el mapa
  y abrir la ficha;
* enlace a la fuente original en cada resultado;
* aviso metodológico: la búsqueda recorre solo los contratos
  analizados, no todo SECOP.

### Capa determinística

Obligatoria. Debe funcionar sin clave de modelo.

Busca en:

* nombre de municipio;
* objeto / fragmento;
* marcas de calamidad;
* año;
* términos ya normalizados en `config.py`.

### Capa de IA

Solo si la capa determinística no basta para interpretar la
pregunta.

El modelo puede:

* extraer municipio, año, tema y si se pide calamidad;
* proponer términos equivalentes que ya existan en el
  vocabulario de `config.py`;
* elegir, entre coincidencias reales, cuáles mostrar primero;
* devolver el fragmento literal que hace pertinente el
  resultado.

El modelo no puede:

* inventar un `id_contrato`;
* completar un objeto contractual;
* afirmar un municipio que no esté en el resultado;
* decir que "no hubo inversión" si la lista queda vacía;
* responder con conocimiento externo ("en 2022 hubo un
  deslizamiento en…").

Si la lista queda vacía, el texto es:

```text
No se encontraron contratos identificados en el conjunto
analizado que coincidan con esta pregunta.
```

Nunca:

```text
No hay inversión
No se contrataron obras
```

### Verificación de cada resultado

Antes de mostrar un resultado producido o reordenado por el modelo:

```text
id_contrato ∈ datos.json
    ↓
fragmento ∈ objeto o texto original
    ↓
¿existe?
    ├── sí → mostrar
    └── no → descartar
```

## Salida obligatoria

```text
Campo de búsqueda usable
+
Resultados solo del conjunto curado
+
Fragmento literal por coincidencia
+
Enlace a SECOP
+
Degradación a palabras clave si falla la IA
```

## Criterio de aceptación

Una persona ajena al proyecto debe poder escribir una pregunta
sin jerga y llegar a un contrato verificable, o entender con
claridad que ese contrato no está en el conjunto analizado.

El mapa y la ficha siguen funcionando si se apaga la capa de IA.

## Punto de decisión

Si la interpretación con IA inventa coincidencias o no sobrevive
la verificación de fragmento:

```text
APAGAR LA CAPA DE IA.
DEJAR SOLO LA BÚSQUEDA POR PALABRAS CLAVE.
```

No se improvisa un buscador "más inteligente" menos verificable.

La Fase 7B no bloquea la Fase 7. Si falta tiempo, el producto
se demuestra sin ella.

---

# FASE 8 — Verificación independiente

## Objetivo

Separar la construcción de los datos de la selección de la evidencia.

La persona que construyó el pipeline no selecciona los casos principales de la
demostración.

## Selección de casos

Buscar al menos:

### Caso A — Señal territorial

Un municipio donde la combinación de variables produzca una pregunta
interesante.

La formulación debe mantenerse dentro del alcance:

> Esto no demuestra que algo esté mal. Muestra una señal que merece ser
> investigada.

### Caso B — Prueba tecnológica

Un contrato donde:

* el texto sea real;
* la ubicación sea específica;
* el fragmento sea claro;
* el enlace permita verificar la fuente.

### Caso C — Caso contradictorio

Incluir deliberadamente un caso que no confirme la narrativa más dramática.

Puede ser:

* buena cobertura;
* contratación abundante;
* ausencia de calamidad citada;
* una combinación que obligue a matizar.

---

## Protocolo de verificación

Para cada dato mostrado:

1. abrir `urlproceso`;
2. localizar el contrato;
3. confirmar el objeto contractual;
4. confirmar el fragmento;
5. confirmar valor si se muestra;
6. confirmar municipio;
7. registrar el resultado.

Formato:

```text
CASO:
ID:
MUNICIPIO:
DATO MOSTRADO:
FUENTE:
VERIFICADO: SÍ / NO
OBSERVACIÓN:
```

Si un dato no puede verificarse:

```text
NO SE MUESTRA
```

---

# FASE 9 — Pulido del producto

## Objetivo

Eliminar fricción sin introducir funcionalidades nuevas.

## Prioridad 1 — Comprensión

Preguntas que una persona ajena al proyecto debe poder responder:

* ¿Qué estoy viendo?
* ¿Qué representa el color?
* ¿Qué representa el borde?
* ¿Qué significa estar rayado?
* ¿Qué significa "sin contratación identificada"?
* ¿Cómo verifico un dato?
* ¿Qué no puede demostrar esta herramienta?

Si la interfaz no responde una de estas preguntas, se corrige.

---

## Prioridad 2 — Legibilidad

Revisar:

* contraste;
* tamaño de tipografía;
* jerarquía;
* espacios;
* scroll;
* estados de hover;
* municipio seleccionado;
* comportamiento en resolución de proyector.

---

## Prioridad 3 — Lenguaje

Eliminar:

```text
"no hubo inversión"
"municipio abandonado"
"dinero perdido"
"corrupción"
"irregularidad detectada"
```

Preferir:

```text
"sin contratación identificada en los contratos analizados"
"cita una declaratoria de calamidad"
"señal que merece investigación"
"verificar en SECOP"
```

---

# 4. Gestión de fallos

LADERA debe degradarse, no colapsar.

| Fallo                  | Comportamiento                       |
| ---------------------- | ------------------------------------ |
| SECOP lento            | detener descarga y mostrar error     |
| Timeout                | no continuar silenciosamente         |
| Descarga parcial       | no tratar como conjunto completo     |
| Cobertura baja         | ajustar filtro localmente            |
| Sin API de IA          | continuar sin extracción ni interpretación de búsqueda |
| Lote de IA falla       | registrar y continuar                |
| Búsqueda IA falla      | degradar a palabras clave            |
| Búsqueda sin coincidencias | decir "no hay coincidencia en el conjunto analizado", nunca "no hay inversión" |
| Fragmento inexistente  | descartar respuesta                  |
| IA alucina demasiado   | apagar extracción                    |
| Valor absurdo          | excluir o enviar a revisión          |
| Municipio no resoluble | registrar y excluir según regla      |
| Datos sin cifra        | contar, no sumar                     |
| Mapa sin internet      | seguir funcionando con GeoJSON local |

El producto mínimo garantizado es:

```text
MAPA MUNICIPAL
+
CONTRATOS IDENTIFICADOS
+
MONTOS CUANDO EXISTEN
+
MARCA DE CALAMIDAD
+
LIMITACIONES
```

La extracción submunicipal y la búsqueda asistida mejoran el producto,
pero no pueden convertirse en un punto único de fallo.

---

# 5. Estrategia de trabajo del equipo

## Rol A — Datos

Responsable de:

* `config.py`;
* `pipeline/`;
* `data/`;
* cobertura;
* calidad;
* `datos.json`.

No se detiene para hacer frontend.

---

## Rol B — Frontend

Responsable de:

* `web/index.html`;
* `web/estilos.css`;
* `web/app.js`;
* `web/servidor.py`;
* la caja de búsqueda y su degradación a palabras clave.

Empieza inmediatamente con datos ficticios.

No espera datos reales.

---

## Rol C — Calidad y producto

Responsable de:

* `docs/`;
* bitácora de decisiones;
* pruebas;
* verificación contra SECOP;
* selección independiente de casos;
* verificación de que la búsqueda no inventa coincidencias;
* narrativa;
* demo.

No es "apoyo".

Su trabajo evita que el equipo presente como evidencia algo que solo fue
generado correctamente desde el punto de vista técnico.

---

# 6. Protocolo de integración entre personas

## Comunicación

Cada vez que una persona termina un artefacto:

1. lo guarda;
2. lo ejecuta;
3. comparte cómo reproducirlo;
4. registra el commit;
5. la siguiente persona consume la salida.

Nunca:

```text
"ya casi está"
"funciona en mi computador"
"solo falta conectar"
```

sin artefacto verificable.

---

## Commits mínimos

Ejemplos:

```text
chore: initialize repository structure
feat(data): add indexed SECOP downloader
feat(data): add local thematic filtering
feat(data): add data quality curation
feat(ai): add verified location extraction
feat(data): generate canonical datos.json
feat(web): render Antioquia municipalities
feat(web): add municipal detail panel
test(data): validate 125 municipality invariant
docs: add verified demo cases
```

Evitar commits gigantes que mezclen:

* pipeline;
* frontend;
* estilos;
* datos;
* cambios metodológicos.

---

# 7. Checklist de integración final

## Pipeline

* [ ] `p1_bajar.py` termina correctamente.
* [ ] `p2_filtrar.py` puede repetirse sin red.
* [ ] `p3_curar.py` produce los tres destinos.
* [ ] `p4_ia.py` puede fallar sin romper el proyecto.
* [ ] `p5_json.py` valida invariantes.
* [ ] `datos.json` existe.

## Datos

* [ ] 125 municipios.
* [ ] cero claves duplicadas.
* [ ] ningún contrato duplicado.
* [ ] conteos consistentes.
* [ ] montos consistentes.
* [ ] contratos sin cifra preservados.
* [ ] lugares con fragmento.
* [ ] URLs presentes donde corresponde.

## Frontend

* [ ] mapa carga.
* [ ] `fitBounds` funciona.
* [ ] hover funciona.
* [ ] clic funciona.
* [ ] resumen coincide con JSON.
* [ ] tres estados municipales son distinguibles.
* [ ] calamidad usa un canal independiente.
* [ ] lugares muestran evidencia.
* [ ] enlaces abren la fuente.
* [ ] limitaciones son visibles.
* [ ] la búsqueda por palabras clave funciona sin IA.
* [ ] la búsqueda asistida, si está encendida, solo devuelve
      contratos del conjunto curado con fragmento verificable.

## Demo

* [ ] caso principal verificado.
* [ ] caso tecnológico verificado.
* [ ] caso contradictorio verificado.
* [ ] pitch ensayado.
* [ ] aplicación probada en pantalla objetivo.
* [ ] recorrido de respaldo disponible.

---

# 8. Cronograma operativo para una ventana de 10 horas

Este cronograma no sustituye las fases. Las comprime.

## 0:00–0:30 — Arranque

### A

* estructura;
* `config.py`;
* `comun.py`;
* iniciar `p1_bajar.py`.

### B

* servidor;
* GeoJSON;
* fixture.

### C

* leer criterios del evento;
* abrir `DECISIONES.md`;
* preparar plantilla de verificación.

### Checkpoint

```text
Servidor arriba
+
Descarga iniciada o terminada
+
Mapa visible
```

---

## 0:30–1:30 — Producto visible

### A

* terminar ingesta;
* validar columnas;
* cachear crudo.

### B

* mapa;
* estados;
* panel;
* caja de búsqueda por palabras clave.

### C

* revisar lenguaje;
* preparar matriz de casos.

### Checkpoint

```text
Mapa completamente funcional con datos ficticios.
```

---

## 1:30–3:00 — Cobertura

### A

* `p2_filtrar`;
* medir municipios;
* iterar vocabulario localmente.

### B

* ficha;
* resumen;
* lugares;
* limitaciones.

### C

* revisar resultados tempranos;
* detectar anomalías evidentes.

### Checkpoint

```text
Cobertura medida.
Datos reales ya existen en forma procesable.
```

---

## 3:00–5:00 — Calidad

### A

* `p3_curar`;
* revisión manual;
* clasificación de obra.

### B

* conectar estructura final de JSON;
* preparar estados reales.

### C

* empezar verificación de una muestra.

### Checkpoint

```text
Conjunto limpio.
Estados de municipio definidos.
```

---

## 5:00–6:30 — IA y extracción

### A

* ejecutar extracción;
* verificar fragmentos;
* medir tasa de descarte.

### B

* terminar representación de lugares.

### C

* revisar las primeras ubicaciones aceptadas.

### Punto de decisión

Si la extracción no es confiable:

```text
APAGARLA.
```

No gastar el resto del tiempo intentando salvar una característica que no es
necesaria para que el mapa funcione.

---

## 6:30–7:30 — Integración real

### A

* `p5_json.py`;
* validación de 125 municipios.

### B

* reemplazar fixture por datos reales;
* comprobar que la búsqueda por palabras clave sigue
  funcionando con el JSON real.

### C

* comprobar números y casos.

### Checkpoint

```text
La aplicación completa funciona con datos reales.
```

Este es el punto más importante del proyecto.

Si ese checkpoint se cumple y sobra tiempo, B conecta la
interpretación con IA (Fase 7B). Si no, la búsqueda se queda
en palabras clave. No se retrasa la verificación por esto.

---

## 7:30–8:30 — Verificación

### C lidera

* verificar casos;
* elegir caso principal;
* elegir caso tecnológico;
* incluir caso contradictorio.

A y B corrigen únicamente errores que bloqueen la demostración.

---

## 8:30–9:15 — Pulido

Solo:

* legibilidad;
* bugs;
* copy;
* jerarquía;
* rendimiento.

No features nuevas.

---

## 9:15–10:00 — Congelación

* grabar o preparar respaldo;
* ensayo completo;
* comprobar enlaces;
* congelar código;
* no tocar arquitectura;
* no cambiar datos salvo error verificable.

Último checkpoint:

```text
¿Podemos demostrar LADERA ahora mismo
sin escribir una sola línea más?
```

Si la respuesta es sí, se termina.

---

# 9. Criterios de prioridad

Cuando falte tiempo:

## P0 — No negociable

1. Datos reales.
2. 125 municipios.
3. Pipeline reproducible.
4. Tres estados.
5. Mapa interactivo.
6. Limitaciones.
7. Verificación de datos mostrados.

## P1 — Muy importante

8. Extracción submunicipal verificable.
9. Búsqueda asistida sobre el conjunto analizado.
10. Casos destacados.
11. Solicitud de información.
12. Narrativa pulida.

## P2 — Solo si todo lo anterior funciona

13. Animaciones.
14. Explicaciones generadas.
15. Refinamiento visual adicional.
16. Métricas extra.
17. Nuevas capas.

La regla es simple:

> **Nunca sacrificar P0 para construir P2.**

---

# 10. Antipatrones prohibidos

## No hacer

### Reescribir la arquitectura

El pipeline por archivos ya resuelve:

* reanudación;
* inspección;
* determinismo;
* velocidad de desarrollo.

No introducir una base de datos durante la construcción.

### Usar IA para sumar o decidir cifras

Los números pertenecen a código determinístico.

### Corregir datos silenciosamente

Nunca convertir:

```text
valor absurdo → valor que "parece razonable"
```

### Mostrar una extracción sin evidencia

No importa si "seguramente es correcta".

Sin fragmento:

```text
NO ENTRA.
```

### Dejar que la búsqueda invente o sentencie

La búsqueda no es una autoridad. Si el modelo propone un contrato
que no está en el conjunto, o un fragmento que no aparece en el
texto, el resultado no se muestra.

Una lista vacía significa "no hay coincidencia en lo analizado".
No significa "no hubo obra" ni "no hubo inversión".

### Esperar a los datos para construir la interfaz

El frontend trabaja desde el principio.

### Mostrar "cero" como "sin inversión"

Cero contratos identificados no equivale a cero inversión real.

### Seguir agregando funcionalidades

Una funcionalidad nueva debe responder:

> ¿Hace que el usuario pueda responder una pregunta que actualmente no puede?

Si no, queda para después.

---

# 11. Qué ocurre después del MVP

Estas líneas no forman parte de la construcción inicial.

Solo se consideran cuando el núcleo esté estable.

## Posibles extensiones

* otros departamentos;
* rango temporal configurable;
* otros tipos de contrato;
* actualización automática;
* mayor cobertura temática;
* historial temporal;
* exportación de resultados;
* más tipos de evidencia territorial;
* comparación entre periodos;
* herramientas de investigación;
* mejoras de accesibilidad;
* arquitectura de actualización programada.

Ninguna de estas extensiones puede modificar retrospectivamente las reglas que
hicieron reproducible la primera versión.

---

# 12. Cierre

LADERA no se construye acumulando funcionalidades.

Se construye asegurando esta cadena:

```text
FUENTE PÚBLICA
    ↓
DESCARGA REPRODUCIBLE
    ↓
FILTRADO EXPLÍCITO
    ↓
CURACIÓN TRAZABLE
    ↓
EXTRACCIÓN VERIFICABLE
    ↓
AGREGACIÓN DETERMINISTA
    ↓
MAPA COMPRENSIBLE
    ↓
VERIFICACIÓN CONTRA LA FUENTE
    ↓
PREGUNTA INVESTIGABLE
```

El proyecto fracasa si se rompe la confianza en cualquier eslabón central.

El proyecto funciona si una persona puede hacer este recorrido:

```text
ver un patrón
    ↓
seleccionar un municipio
    ↓
entender qué significa
    ↓
ver el contrato o la evidencia textual
    ↓
abrir la fuente oficial
    ↓
formular una pregunta mejor informada
```

Ese es el horizonte.

No construir una herramienta que "parece" investigar la contratación.

Construir una herramienta donde cada afirmación importante pueda recorrer el
camino inverso hasta el registro público que la sostiene.

```
```


Yo usaría este como el **`PLAN.md` definitivo**. Lo que me gusta es que ya no depende de una narrativa optimista de “seguro logramos hacer X”: cada fase tiene **entrada, salida, criterio de aceptación y punto de decisión**.

La separación queda bastante limpia:

* **La especificación canónica** = qué es LADERA y cuáles son sus reglas.
* **`PLAN.md`** = cómo se construye sin perderse.
* **`CONTRATO.md`** = cómo se hablan datos y frontend.
* **`DECISIONES.md`** = qué se descarta o aplaza sin volver a abrir debates.

Y hay una idea que yo mantendría como regla absoluta: **la Fase 7 —datos reales en pantalla— es el verdadero momento de éxito del proyecto**. Todo lo demás, incluida la extracción con IA y el pulido, es secundario hasta que eso exista.
