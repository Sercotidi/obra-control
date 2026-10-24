# ObraControl

MVP para gestionar avances de obra, cortes y cobros de contratistas (FastAPI + Pydantic + CSV).

Proyecto de la materia Desarrollo de Software Con profesor SIGMOTOA.

## Mapa de endpoints

ObraControl dispone de **35 endpoints** para gestionar contratos, actividades, cortes, facturas y pagos.

| Modelo | Cantidad |
|---|---:|
| Contratos | 8 |
| Actividades | 8 |
| Cortes | 7 |
| Facturas | 7 |
| Pagos | 5 |
| **Total** | **35** |

**Métodos:** 🟢 GET · 🔵 POST · 🟡 PUT · 🟠 PATCH · 🔴 DELETE

**Códigos HTTP:** `200` OK · `201` Creado · `204` Sin contenido · `404` No encontrado · `409` Conflicto de negocio · `422` Datos inválidos.

### Contratos (8)

| Método | Ruta | Descripción | Parámetros | Respuestas | Regla |
|---|---|---|---|---|---|
| 🔵 POST | `/contratos` | Crear | JSON | 201, 409, 422 | Número único, fechas válidas, valor positivo |
| 🟢 GET | `/contratos` | Listar | estado, contratista, activo | 200, 422 | Filtros |
| 🟢 GET | `/contratos/historico` | Históricos | — | 200 | Inactivos |
| 🟢 GET | `/contratos/numero/{numero_contrato}` | Buscar número | numero_contrato | 200, 404 | Número existente |
| 🟢 GET | `/contratos/{contrato_id}` | Consultar | ID | 200, 404 | Debe existir |
| 🟡 PUT | `/contratos/{contrato_id}` | Actualizar | ID, JSON | 200, 404, 409, 422 | Número único |
| 🔴 DELETE | `/contratos/{contrato_id}` | Eliminar | ID | 204, 404, 409 | Sin cortes vigentes |
| 🟢 GET | `/contratos/{contrato_id}/resumen` | Resumen financiero | ID | 200, 404 | Calcula valores y saldos |

### Actividades (8)

| Método | Ruta | Descripción | Parámetros | Respuestas | Regla |
|---|---|---|---|---|---|
| 🔵 POST | `/actividades` | Crear | JSON | 201, 404, 409, 422 | Contrato activo; no supera su valor |
| 🟢 GET | `/actividades` | Listar | contrato_id, nombre, activo | 200, 422 | Filtros |
| 🟢 GET | `/actividades/historico` | Históricos | — | 200 | Inactivas |
| 🟢 GET | `/actividades/{actividad_id}` | Consultar | ID | 200, 404 | Debe existir |
| 🟡 PUT | `/actividades/{actividad_id}` | Actualizar | ID, JSON | 200, 404, 409, 422 | Respeta cantidades cortadas |
| 🔴 DELETE | `/actividades/{actividad_id}` | Eliminar | ID | 204, 404, 409 | Sin avance ejecutado |
| 🟢 GET | `/actividades/{actividad_id}/cantidades` | Consultar cantidades | ID | 200, 404 | Calcula disponibilidad |
| 🟠 PATCH | `/actividades/{actividad_id}/avance` | Registrar avance | ID, cantidad_ejecutada | 200, 404, 409, 422 | No supera lo contratado ni baja de lo cortado |

### Cortes (7)

| Método | Ruta | Descripción | Parámetros | Respuestas | Regla |
|---|---|---|---|---|---|
| 🔵 POST | `/cortes` | Crear con detalles | JSON | 201, 404, 409, 422 | Solo cantidades ejecutadas no cobradas; número único por contrato |
| 🟢 GET | `/cortes` | Listar | contrato_id, estado, activo | 200, 422 | Filtros |
| 🟢 GET | `/cortes/historico` | Históricos | — | 200 | Inactivos |
| 🟢 GET | `/cortes/{corte_id}` | Consultar detalles y total | ID | 200, 404 | Total calculado |
| 🟡 PUT | `/cortes/{corte_id}` | Editar | ID, JSON | 200, 404, 409, 422 | Solo borrador |
| 🔴 DELETE | `/cortes/{corte_id}` | Eliminar | ID | 204, 404, 409 | Solo borrador; libera cantidades |
| 🟠 PATCH | `/cortes/{corte_id}/estado` | Cambiar estado | ID, nuevo_estado | 200, 404, 409, 422 | Flujo de aprobación válido |

### Facturas (7)

| Método | Ruta | Descripción | Parámetros | Respuestas | Regla |
|---|---|---|---|---|---|
| 🔵 POST | `/facturas` | Crear | JSON | 201, 404, 409, 422 | Corte aprobado, número único, valor válido |
| 🟢 GET | `/facturas` | Listar | contrato_id, corte_id, activo | 200, 422 | Filtros |
| 🟢 GET | `/facturas/historico` | Históricos | — | 200 | Inactivas |
| 🟢 GET | `/facturas/numero/{numero_factura}` | Buscar número | numero_factura | 200, 404 | Número existente |
| 🟢 GET | `/facturas/{factura_id}` | Consultar saldo | ID | 200, 404 | Valor menos pagos activos |
| 🟡 PUT | `/facturas/{factura_id}` | Actualizar | ID, JSON | 200, 404, 409, 422 | Sin pagos |
| 🔴 DELETE | `/facturas/{factura_id}` | Eliminar | ID | 204, 404, 409 | Sin pagos |

### Pagos (5)

| Método | Ruta | Descripción | Parámetros | Respuestas | Regla |
|---|---|---|---|---|---|
| 🔵 POST | `/pagos` | Registrar pago | JSON | 201, 404, 409, 422 | No supera saldo ni precede fecha de factura |
| 🟢 GET | `/pagos` | Listar | factura_id, activo | 200, 422 | Filtros |
| 🟢 GET | `/pagos/{pago_id}` | Consultar | ID | 200, 404 | Debe existir |
| 🟡 PUT | `/pagos/{pago_id}` | Actualizar | ID, JSON | 200, 404, 409, 422 | Revalida saldo |
| 🔴 DELETE | `/pagos/{pago_id}` | Eliminar | ID | 204, 404 | Deja de contar como recaudado |

### Ejemplos JSON

**POST `/contratos`**

```json
{
  "numero_contrato": "C-001",
  "nombre_obra": "Campus FUCS",
  "empresa_cliente": "Cliente SA",
  "nombre_contratista": "Muros Ltda",
  "fecha_inicio": "2026-01-01",
  "fecha_fin": "2026-12-31",
  "valor_contrato": 5000000,
  "estado": "activo"
}
```

**POST `/cortes`**

```json
{
  "contrato_id": 1,
  "numero_corte": 1,
  "fecha_corte": "2026-03-01",
  "periodo_inicio": "2026-02-01",
  "periodo_fin": "2026-02-28",
  "detalles": [
    {"actividad_id": 1, "cantidad": 2}
  ]
}
```

**Respuesta resumida — `201 Created`**

```json
{
  "id": 1,
  "estado": "borrador",
  "activo": true,
  "detalles": [
    {"actividad_id": 1, "cantidad": 2}
  ],
  "valor_total": 2000000
}
```