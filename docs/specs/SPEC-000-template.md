# SPEC-000 · Plantilla de especificación

> Copiar esta plantilla para cada nuevo componente. Una spec es *contrato de
> comportamiento*: describe **qué** hace el componente y **cómo se acepta**, no el
> detalle de implementación.

---

## Encabezado

- **ID:** SPEC-xxx
- **Título:**
- **Estado:** Borrador | Aprobado | Obsoleto
- **Requisitos cubiertos:** FR-xx, NFR-xx
- **Depende de / Contratos:** enlaces a [data-contracts.md](../contracts/data-contracts.md) u otras specs

## 1. Objetivo
Una o dos frases: qué problema resuelve y para quién.

## 2. Entradas y salidas
Parámetros, ficheros de entrada/salida, configuración, valores por defecto.

## 3. Comportamiento
Descripción funcional. Reglas de negocio. Algoritmos clave (referenciar dominio).

## 4. Interfaz pública (diseño)
Firmas de funciones/clases relevantes (tipadas). No es implementación.

## 5. Manejo de errores
Qué puede fallar, qué excepción se lanza, qué código de salida, qué se registra.

## 6. Criterios de aceptación (Gherkin)
```gherkin
Feature: <capacidad>
  Scenario: <caso>
    Given <precondición>
    When <acción>
    Then <resultado observable y verificable>
```

## 7. Pruebas asociadas
Lista de pruebas (unit/integration/e2e) que verifican los criterios.

## 8. Trazabilidad
Enlace a la [RTM](../requirements/requirements-traceability-matrix.md) y a los FR/NFR.
