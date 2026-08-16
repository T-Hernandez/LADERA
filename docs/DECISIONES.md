# Decisiones

## 2026-08-15 — Un solo proceso Flask en `web/`

**Decisión:** la Fase 1 se sirve con `web/servidor.py`. No se abre `/apps` + `/services/api`.

**Motivo:** el plan pide esa separación cuando haya un API y un frontend que evolucionen aparte. Hoy el producto es un mapa + un JSON.

**Impacto:** el frontend solo habla con `/api/datos` y `/api/reportes`. Si más adelante se parte el servicio, esas rutas se mantienen.

**Descartado:** montar dos procesos vacíos para parecer una plataforma.

## 2026-08-15 — Mapa local, sin teselas externas

**Decisión:** Leaflet + `municipios_antioquia.geojson`. Sin OpenStreetMap ni otra capa base.

**Motivo:** el mapa tiene que funcionar sin red.

**Descartado:** cargar `co_2018_MGN_MPIO_POLITICO.geojson` en el navegador (es la capa nacional).

## 2026-08-15 — Fixture antes que SECOP

**Decisión:** la Fase 1 no llama a datos.gov.co.

**Motivo:** el ciclo de interfaz no puede esperar la ingesta. Los 125 municipios ya existen en el JSON, con ceros.

**Impacto:** reemplazar el fixture por datos reales no debe exigir reescribir `app.js`.

## 2026-08-15 — Reportes locales aparte del fixture

**Decisión:** lo que se crea en “Reportar” se guarda en `data/interim/reportes_locales.json` y se fusiona al servir `/api/datos`.

**Motivo:** no editar a mano el fixture. El crudo (cuando exista) y el fixture no se sobrescriben.

## 2026-08-15 — Piloto territorial: Antioquia, 125 municipios

**Decisión:** el primer mapa es Antioquia. La llave es el código DANE.

**Motivo:** ya existen el GeoJSON recortado y el diccionario de municipios.

## 2026-08-15 — El modelo vive en `modelo/`, no en una base de datos

**Decisión:** la Fase 2 es un paquete Python que construye y valida entidades. El intercambio sigue siendo `datos.json`.

**Motivo:** todavía no hay ingesta real. Una base de datos ahora mezclaría persistencia con reglas.

**Impacto:** `construir_fixture.py` y `web/servidor.py` no escriben diccionarios a mano. Si el dato no pasa el modelo, no se sirve.

**Descartado:** confirmar una relación solo porque la IA la afirmó.

## 2026-08-15 — Ingesta solo por datos.gov.co, consulta piloto congelada

**Decisión:** `pipeline/ingestion/bajar.py` consulta `jbjy-vk9h` con

`departamento='Antioquia' AND tipo_de_contrato='Obra' AND fecha_de_firma>='2019-01-01'`.

**Motivo:** SECOP es la fuente; datos.gov.co es el tubo. No se scrapea `community.secop.gov.co`. `urlproceso` se lee, no se construye.

**Impacto:** el crudo queda en `data/raw/contratos_YYYY_MM_DD.csv` y el manifiesto en `data/metadata/ingestion_manifest.json`. Un día no pisa el archivo anterior. Cambiar el filtro no exige reescribir el frontend.

**Descartado:** tratar una descarga parcial como conjunto completo.

## 2026-08-15 — Curación sin estimar valores

**Decisión:** `pipeline/processing/curar.py` clasifica cada fila en LIMPIO / REVISAR / EXCLUIDO. Un valor raro no se reemplaza. Cero cuenta como contrato y no suma. Los montos enormes no se descartan solo por tamaño: no hay contradicción aritmética en el crudo.

**Motivo:** la Fase 4 pide motivo rastreable, no una cifra que “parezca razonable”.

**Impacto:** el frontend no cambia. La Fase 5 parte de `data/interim/contratos_limpios.csv`.

**Descartado:** deduplicar por nombre de entidad o municipio.

## 2026-08-15 — Territorio por DANE, sin IA que invente el lugar

**Decisión:** `pipeline/processing/resolver.py` cruza el objeto y la ciudad con `municipios_lookup.json`. El DANE sale de un nombre oficial, de un alias único (Don Matías, Santa Fe de Antioquia, San Vicente) o queda AMBIGUO / SIN_RESOLVER. Un MULTIMUNICIPIO guarda todos los códigos y no parte el valor. La vereda o el barrio solo se anotan si el fragmento está en el objeto.

**Motivo:** la Fase 5 pregunta qué contratos estuvieron activos en un territorio y un periodo. Eso no autoriza a adivinar el municipio ni a mandar SECOP al mapa.

**Impacto:** el frontend no cambia. La salida es `data/interim/contratos_resueltos.csv`.

**Descartado:** alias cortos como “San Pedro” o “El Carmen”. Dos municipios los comparten.

## 2026-08-15 — Un reporte no necesita contrato

**Decisión:** `reportes/almacen.py` crea una observación con descripción, categoría, punto, municipio automático (polígono DANE), fecha de lo observado y, si viene, una foto en disco. El alta queda `EN_REVISION`. La fecha de creación la pone el servidor. Un `contrato_id` en el formulario se ignora.

**Motivo:** la Fase 6 pide un reporte completo sin conocer contratación. La foto no viaja dentro del texto. Vincular reporte y contrato es la Fase 7.

**Impacto:** `/api/reportes` acepta multipart. `/api/territorio` resuelve el municipio del clic. El mapa, en “Reportar”, coloca y arrastra el punto en vez de abrir el municipio.

**Descartado:** pedir el contrato al reportar, incrustar la imagen en el JSON, o tratar el envío como un hecho verificado.

## 2026-08-15 — El motor sugiere; una persona confirma

**Decisión:** `relaciones/motor.py` puntúa territorio, tiempo, categoría y un solape de palabras. Sin municipio compartido no hay sugerencia. El motor solo escribe `SUGERIDA` con método `REGLAS`. Confirmar o indicar el contrato es un acto humano (`MANUAL` o `DIRECTA`). La IA no entra.

**Motivo:** la Fase 7 pide ver “posible relación” frente a “relación confirmada”. Un porcentaje no basta: cada vínculo lleva una evidencia en lenguaje concreto.

**Impacto:** `/api/datos` fusiona fixture + decisiones locales + sugerencias nuevas. Las decisiones quedan en `data/interim/relaciones_locales.json`.

**Descartado:** confirmar por IA, pintar una sugerencia como hecho, o exigir un contrato para crear el reporte.
