# 🏗️ ObraControl

**API para la gestión de contratos de obra, actividades y cortes de cobro.**

Desarrollada con **FastAPI, SQLModel y SQLite** para la materia de Desarrollo de Software (profesor SIGMOTOA).

---

## 🎯 ¿Qué hace?

Permite a una constructora administrar sus contratos con subcontratistas, registrar las actividades ejecutadas y gestionar los cortes de cobro por los trabajos realizados.

| 📑 Contratos | 🧱 Actividades | 💰 Cortes |
|---|---|---|
| Datos y valores de la obra | Cantidades y precios | Solicitudes de cobro y estados |

## 🚀 Instalación y ejecución

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 🔗 Accesos

| Recurso | Dirección |
|---|---|
| 📘 Documentación y pruebas | http://127.0.0.1:8000/docs |
| 🗄️ Base de datos visual | http://127.0.0.1:8000/base-de-datos |
| 🧪 Pruebas automáticas | `python -m pytest -q` |

## 📂 Estructura del proyecto

```text
ObraControl/
├── app/
│   ├── main.py          # Inicio de la API
│   ├── database.py      # Conexión a SQLite
│   ├── models.py        # Modelos de datos
│   └── routers/
│       ├── contratos.py
│       ├── actividades.py
│       ├── cortes.py
│       └── vista.py
├── tests/
│   └── test_api.py      # Pruebas automáticas
├── requirements.txt
└── README.md
```

## 🗃️ Modelos de datos

| Modelo | Información principal |
|---|---|
| 📑 `contrato` | Obra, cliente, contratista, fechas y valor |
| 🧱 `actividad` | Unidad, cantidades y precio unitario |
| 💵 `corte` | Número, fecha, valor, estado y observaciones |

**Relación:** un contrato puede tener múltiples actividades y cortes.

Estados de un corte: `presentado` · `aprobado` · `rechazado`.

## 🔌 Mapa de endpoints

| Método | Ruta | Función |
|---|---|---|
| `POST` | `/contratos` | Crear contrato |
| `GET` | `/contratos` | Listar y filtrar |
| `GET` | `/contratos/{id}` | Consultar contrato |
| `PUT` | `/contratos/{id}` | Actualizar contrato |
| `DELETE` | `/contratos/{id}` | Desactivar contrato |
| `POST` | `/actividades` | Crear actividad |
| `GET` | `/actividades` | Listar y filtrar |
| `GET` | `/actividades/{id}` | Consultar actividad |
| `PUT` | `/actividades/{id}` | Actualizar actividad |
| `DELETE` | `/actividades/{id}` | Desactivar actividad |
| `POST` | `/cortes` | Crear corte |
| `GET` | `/cortes` | Listar y filtrar |
| `GET` | `/cortes/{id}` | Consultar corte |
| `PUT` | `/cortes/{id}` | Actualizar corte |
| `DELETE` | `/cortes/{id}` | Desactivar corte |
| `GET` | `/base-de-datos` | Visualizar las tablas |

*Los contratos también permiten buscar por número mediante `/contratos/numero/{numero_contrato}`.*

## ⚙️ Reglas de negocio

- 📚 **Histórico:** los registros se desactivan sin borrar su historial.
- 🔒 **Protección:** no se eliminan contratos con cortes activos ni actividades con avance ejecutado.
- ✅ **Cortes aprobados:** no se pueden modificar ni eliminar.
- 🔢 **Validación:** no se repiten números de contrato ni números de corte dentro del mismo contrato.
- 📏 **Cantidades:** lo ejecutado no puede superar lo contratado.
- 💵 **Valores:** un corte no puede superar el valor del contrato.
- 🔗 **Integridad:** actividades y cortes requieren contratos existentes y activos.

## ⚠️ Manejo de errores

| Código | Significado |
|---|---|
| `404` | Registro no encontrado |
| `409` | Conflicto con una regla de negocio |
| `422` | Datos inválidos o inconsistentes |

La API responde con mensajes de error controlados para facilitar la identificación de problemas.

---

**🛠️ Tecnologías:** Python · FastAPI · SQLModel · SQLite · Pytest