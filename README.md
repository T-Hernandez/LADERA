# LADERA

Plataforma de trazabilidad ciudadana: un registro de lo que las personas observan en el territorio, al lado de la contratación pública que normalmente es difícil de recorrer.

Esta versión cubre la **Fase 1** (mapa + fixture), la **Fase 2** (modelo) y la **Fase 3** (ingesta). La interfaz sigue usando el fixture hasta la curación.

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
```

## Qué probar

1. **Explorar** → Medellín: contratos + reporte con foto + relación sugerida.
2. Medellín → contrato **FIX-X** → reporte relacionado.
3. **Bello**: contratos, cero reportes.
4. **Ituango**: reporte sin relación contractual conocida.
5. **Reportar**: crea una observación; queda en `data/interim/reportes_locales.json`.
6. **Buscar**: `Popular`, `Niquía`, `movimiento en masa`.

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

Los contratos reales, cuando existan, salen de SECOP vía datos.gov.co (`jbjy-vk9h`). El enlace de cada hallazgo es el campo `URLProceso`, no una URL inventada.
