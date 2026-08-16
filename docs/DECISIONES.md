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
