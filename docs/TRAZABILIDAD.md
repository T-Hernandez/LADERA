# Trazabilidad — Fase 1

Cada afirmación visible debe poder recorrer el camino inverso.

## Dato público

```text
registro en datos.json
    → fuente (fixture | secop2)
    → url_fuente (URLProceso, si existe)
```

No se construye la URL del expediente a mano. Se lee del campo.

## Observación ciudadana

```text
reporte
    → autor (etiqueta)
    → fecha_creacion
    → fecha_observacion
    → ubicación
    → evidencias[]
    → estado
```

## Relación

```text
relación
    → metodo (DIRECTA | REGLAS | IA | MANUAL)
    → estado (SUGERIDA | CONFIRMADA | DESCARTADA)
    → evidencia (señales concretas, no un porcentaje solo)
```

## Lo que no se afirma

- Un reporte no es un hecho verificado.
- Un contrato no prueba que la obra se ejecutó.
- Una relación sugerida no es responsabilidad ni irregularidad.
- Cero contratos identificados no es “cero inversión”.
