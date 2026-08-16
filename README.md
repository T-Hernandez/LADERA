# LADERA

Plataforma de trazabilidad ciudadana: un registro de lo que las personas observan en el territorio, al lado de la contratación pública que normalmente es difícil de recorrer.

Esta versión cubre hasta la **Fase 8** (mapa de trazabilidad). Los contratos del mapa siguen siendo el fixture.

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
python -m unittest
python -m pipeline.ingestion --solo-contar
python -m pipeline.ingestion
python -m pipeline.processing
python -m pipeline.processing.resolver
```

## Qué probar

1. **Explorar** → Medellín: contratos + reporte con foto + relación sugerida.
2. Medellín → contrato **FIX-X** → reporte relacionado.
3. **Bello**: contratos, cero reportes.
4. **Ituango**: reporte sin relación contractual conocida.
5. **Reportar**: clic en el mapa, fecha de lo observado, foto opcional. No pide un contrato. Queda en revisión en `data/interim/reportes_locales.json`; la foto, si hay, en `data/interim/evidencias/`.
6. **Buscar**: `Popular`, `Niquía`, `movimiento en masa`.
7. Un reporte en Medellín sobre el muro de El Popular debe mostrar una **posible relación** con FIX-X, distinta de una **relación confirmada**. Se puede confirmar, descartar o indicar el contrato a mano.
8. **Mapa**: enciende y apaga contratos, reportes y dinero. Cambia el periodo a 2024, 2025 o 2026. Medellín en 2026 tiene contrato + reporte; en 2024, contrato sin reporte. Eso no demuestra causa. El panel del municipio resume cifra usable, estados y relaciones.

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
| Reportes locales | `data/interim/reportes_locales.json` |
| Fotos de evidencia | `data/interim/evidencias/` |
| Relaciones locales | `data/interim/relaciones_locales.json` |

Los contratos reales, cuando existan, salen de SECOP vía datos.gov.co (`jbjy-vk9h`). El enlace de cada hallazgo es el campo `URLProceso`, no una URL inventada.
