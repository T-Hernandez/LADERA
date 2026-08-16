# LADERA

Plataforma de trazabilidad ciudadana: un registro de lo que las personas observan en el territorio, al lado de la contratación pública que normalmente es difícil de recorrer.

Esta versión cubre hasta la **Fase 13** (escala extensible, aún cerrada). El servidor sirve contratos reales de SECOP II en `data/final/datos.json` en cuanto ese archivo existe (ver "Pipeline de datos reales" abajo); si no existe todavía, cae automáticamente al fixture de demostración en `data/fixtures/datos.json`.

## Cómo correrlo

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python data\fixtures\construir_fixture.py
python web\servidor.py
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000).

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Pipeline de datos reales (opcional)

Descarga contratos reales de SECOP II y los deja listos para el mapa. Cada paso lee la salida del anterior; ninguno sobrescribe al anterior.

```powershell
python -m pipeline.ingestion --solo-contar
python -m pipeline.ingestion
python -m pipeline.processing
python -m pipeline.processing.resolver
python -m pipeline.processing.consolidar
```

El último paso escribe `data/final/datos.json`, que el servidor usa automáticamente a partir de ahí. Los contratos que mencionan varios municipios a la vez, quedan ambiguos, o sin territorio resoluble no se incluyen — el motivo de cada exclusión queda en `data/metadata/consolidacion_manifest.json`, y el conteo se muestra en la pantalla de Inicio.

### Moderación (opcional)

Revisar/retirar un reporte y confirmar/descartar una posible conexión están cerrados por defecto — es un candado de piloto, no un sistema de cuentas (ver `docs/DECISIONES.md`). Para habilitarlo antes de arrancar el servidor:

```powershell
$env:LADERA_MODERACION_TOKEN = "el-token-que-quieras"
```

Sin esta variable, esas rutas responden 401 para todo el mundo, incluso en local. "Señalar" contenido siempre queda abierto, sin token.

### Búsqueda con lenguaje natural (IA opcional, API de Groq)

La búsqueda funciona siempre por reglas (`busqueda/interpretar.py`), sin necesitar IA. Si además defines esta variable antes de arrancar el servidor, LADERA intenta interpretar la pregunta con la API de Groq (nivel gratuito, formato compatible con chat completions), y si la clave falta, la llamada falla, o el modelo devuelve algo que no pasa la validación, cae automáticamente a reglas sin romper la búsqueda:

```powershell
$env:LADERA_IA_CLAVE = "tu-clave-de-groq"
```

(también se acepta la variable estándar `GROQ_API_KEY` como respaldo). Opcionalmente, para cambiar el modelo (por defecto `llama-3.1-8b-instant`):

```powershell
$env:LADERA_IA_MODELO = "llama-3.3-70b-versatile"
```

**La clave nunca va en el repositorio.** No hay ninguna clave hardcodeada en `config.py` ni en ningún otro archivo — solo se lee de la variable de entorno en el momento de arrancar. `.env` está en `.gitignore`. Si nunca defines `LADERA_IA_CLAVE`, LADERA sigue funcionando exactamente igual, solo que la interpretación queda 100% a cargo de las reglas.

El usuario nunca elige entre IA y reglas — LADERA lo decide internamente y siempre expone qué método produjo el resultado (`interpretacion.ia`: `no_configurada`, `usada` o `fallo`). La IA solo puede devolver un JSON de filtros (nunca prosa, nunca inventa contratos ni URLs); ese JSON se valida antes de ejecutarse (`busqueda/consulta.py`).

## Qué probar

La navegación principal es **Inicio / Zona / Buscar / Reportar**. Todo lo interno del
piloto (métricas, escalamiento) vive fuera de ese recorrido, en un panel aparte
enlazado desde Inicio.

Con el fixture de demostración (`python data\fixtures\construir_fixture.py`, sin correr
el pipeline real):

1. **Inicio** → tarjeta "El Popular, Medellín": contrato + reporte con foto + posible conexión sugerida.
2. Medellín → contrato **FIX-X** → reporte con posible conexión.
3. **Bello**: contratos, cero reportes.
4. **Ituango**: reporte sin posible conexión conocida.
7. Un reporte en Medellín sobre el muro de El Popular debe mostrar una **posible conexión** con FIX-X, distinta de una **conexión confirmada**. Confirmar o descartar pide motivo y token de moderación; queda en `data/interim/auditoria.json`.

Con datos reales (después de correr el pipeline completo, ver arriba):

5. **Reportar**: clic en el mapa, fecha de lo observado, foto opcional. No pide un contrato. Queda en revisión en `data/interim/reportes_locales.json`; la foto, si hay, en `data/interim/evidencias/`.
6. **Buscar**: escribe una pregunta en lenguaje corriente. Se ve "LADERA entendió" con los filtros interpretados, luego los contratos, reportes y fuentes. No hay que elegir entre IA y reglas.
8. **Zona**: elige un municipio con el mapa o con el `<select>` (funciona sin mouse). Cambia el periodo a 2024, 2025 o 2026. El panel resume cifra usable, estados, reportes y posibles conexiones.
9. **Confianza**: abre un reporte y lee «¿Por qué este estado?». Señala, retira (pide confirmación) o registra una decisión con motivo — retirar y revisar piden token de moderación, señalar no. "Revisada" no declara irregularidad. Lo descartado o retirado sale del mapa.
10. **Un hilo**: elige una zona y sigue el panel. Desde ahí se agrega evidencia sin perder la zona. Buscar y Reportar no reinician el recorrido.
11. **Panel del piloto**: enlace al final de Inicio, "Panel del piloto (información interna...)". Importa el contraste (reporte útil al lado de un contrato), no el número de usuarios; y ahí mismo, "Hasta dónde se puede crecer" — territorio, fuentes, comunidad, sin abrir el país ni pintar SECOP.

## Datos

| Qué | Dónde |
| --- | --- |
| Polígonos | `municipios_antioquia.geojson` |
| Llave DANE | `municipios_lookup.json` |
| Fixture | `data/fixtures/datos.json` |
| Contrato de campos | `docs/MODELO_DATOS.md` |
| Validación | `modelo/` |
| Ingesta | `python -m pipeline.ingestion` |
| Crudo | `data/raw/contratos_YYYY_MM_DD.csv` |
| Manifiesto | `data/metadata/ingestion_manifest.json` |
| Curación | `python -m pipeline.processing` |
| Limpio / revisar / excluidos | `data/interim/` |
| Resolución territorial | `python -m pipeline.processing.resolver` |
| Contratos resueltos | `data/interim/contratos_resueltos.csv` |
| Consolidación (JSON final) | `python -m pipeline.processing.consolidar` |
| Datos reales que sirve el servidor | `data/final/datos.json` |
| Motivo de exclusiones territoriales | `data/metadata/consolidacion_manifest.json` |
| Reportes locales | `data/interim/reportes_locales.json` |
| Fotos de evidencia | `data/interim/evidencias/` |
| Relaciones locales | `data/interim/relaciones_locales.json` |
| Auditoría | `data/interim/auditoria.json` |
| Decisiones de reportes | `data/interim/reportes_decisiones.json` |
| Eventos del piloto | `data/interim/piloto_eventos.json` |

Los contratos reales, cuando existan, salen de SECOP vía datos.gov.co (`jbjy-vk9h`). El enlace de cada hallazgo es el campo `URLProceso`, no una URL inventada.
