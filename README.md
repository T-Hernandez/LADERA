# LADERA

Plataforma de trazabilidad ciudadana: un registro de lo que las personas observan en el territorio, al lado de la contratación pública que normalmente es difícil de recorrer.

Esta versión es la **Fase 1**: mapa real de los 125 municipios de Antioquia y un fixture de contratos y reportes. Todavía no se descarga SECOP.

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

Los contratos reales, cuando existan, salen de SECOP vía datos.gov.co (`jbjy-vk9h`). El enlace de cada hallazgo es el campo `URLProceso`, no una URL inventada.
