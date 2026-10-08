# DocuSol — Sistema de Gestión Documental V1.1
> **Soluciones Integrales en Gestión, Trazabilidad y Archivo Documental Corporativo**

---

## 1. Descripción General del Proyecto

**DocuSol V1.1** es una plataforma web corporativa de misión crítica diseñada para digitalizar, centralizar y gobernar el flujo documental de organizaciones con estructura descentralizada y múltiples sedes operativas (**Bogotá**, **Medellín** y **Cali**).

La plataforma resuelve de forma integral los desafíos habituales del manejo documental físico y por correo electrónico:
* **Control Estricto de Términos Legales (SLA)**: Monitoreo automatizado con semáforo tricolor para evitar sanciones por vencimientos judiciales (acciones de tutela, derechos de petición y requerimientos administrativos) bajo el calendario legal colombiano.
* **Trazabilidad e Inalterabilidad Absoluta**: Registro cronológico de auditoría (quién, cuándo, desde qué sede y bajo qué observación) para cada radicado, impidiendo modificaciones retroactivas.
* **Cero Pérdida de Expedientes**: Flujo formal y obligatorio de reasignación inter-sedes con confirmación y aceptación en bandeja de entrada receptora.
* **Gobernanza y Aislamiento por Sedes**: Políticas de seguridad y autenticación que garantizan el control perimetral por rol y sede operativa.

---

## 2. Alcance Funcional: Sprints 1 y 2 (HU-001 a HU-010)

El sistema implementa de forma exhaustiva las **10 Historias de Usuario (HU)** correspondientes a los Sprints 1 y 2:

| Sprint | Historia de Usuario | Módulo Funcional | Roles con Acceso |
| :--- | :--- | :--- | :--- |
| **Sprint 1** | **HU-001** | Autenticación y Control Perimetral de Acceso | Todos los roles |
| **Sprint 1** | **HU-002** | Gestión de Cuentas de Usuario y Asignación de Roles | Administrador |
| **Sprint 1** | **HU-003** | Radicación de Documentos e Indización de Metadatos | Radicador, Administrador |
| **Sprint 1** | **HU-004** | Carga y Asociación de Adjuntos Digitales (PDF) | Radicador, Administrador, Gestionador |
| **Sprint 1** | **HU-005** | Reasignación y Traslado Inter-Sedes con Justificación | Radicador, Gestionador, Administrador |
| **Sprint 2** | **HU-006** | Recepción y Aceptación Formal de Expedientes Trasladados | Gestionador, Administrador |
| **Sprint 2** | **HU-007** | Cierre y Finalización de Trámite Documental con PDF | Gestionador, Administrador |
| **Sprint 2** | **HU-008** | Consulta de Trazabilidad e Historial Cronológico Inalterable | Administrador |
| **Sprint 2** | **HU-009** | Generación y Exportación de Reportes Parametrizados (.xlsx) | Administrador, Gestionador |
| **Sprint 2** | **HU-010** | Dashboard de Monitoreo de Vencimientos Legales (Semáforo SLA) | Administrador, Gestionador |

> [!IMPORTANT]
> **Fuente de verdad de los roles: la Propuesta Comercial V1.1.**
> La matriz anterior se corrigió para alinearse con el documento contractual
> firmado, que es el de mayor autoridad del proyecto:
> - **Gestionador** (§"Perfil Gestionador"): *"Recibe, procesa, acepta, traslada o
>   finaliza la gestión del documento"* → el traslado (HU-005) es de los tres
>   perfiles operativos, no solo del Radicador.
> - **Gestionador** (§"Perfil Gestionador"): *"Generación de Reportes
>   Parametrizados... con opción de exportación directa a hojas de cálculo en
>   Excel"* → HU-009 también corresponde al Gestionador, acotado a su sede.
> - **Administrador** (§"Perfil Administrador"): *"asume permisos operacionales
>   de respaldo"* → puede cerrar (HU-007) expedientes de cualquier sede cuando
>   cubre a un gestor ausente.
> - **Administrador** (§"Perfil Administrador"): *"Supervisión del módulo de
>   auditoría y logs de seguridad"* → la bitácora inalterable (HU-008) es una
>   función de supervisión del Administrador, no de consulta abierta.
>
> El README antes decía HU-005 solo para Radicador, HU-007 solo para
> "Administrador de la misma sede" y HU-008/HU-010 para "Todos los roles", lo
> que contradecía tanto a la Propuesta Comercial como a la suite de pruebas
> entregada. La Propuesta Comercial prevalece.

> [!NOTE]
> **Extensibilidad Futura (HU-011 a HU-030)**: El esquema de base de datos relacional (MySQL 8.0 InnoDB), los modelos ORM de SQLAlchemy 2.0 y la arquitectura de componentes de React 18 han sido diseñados de forma desacoplada para admitir los Sprints 3, 4 y 5 sin requerir refactorizaciones que comprometan la funcionalidad existente.

---

## 3. Arquitectura y Stack Tecnológico

DocuSol implementa una arquitectura desacoplada de tres capas contenerizada con Docker:

```
┌────────────────────────────────────────────────────────┐
│           FRONTEND — SPA React 18 + Vite               │
│  - Internacionalización i18n (Inglés por defecto / ES) │
│  - Formatos y Formularios reactivos (Tailwind CSS)     │
│  - Puerto Host: 3000 (Fallback automático 3001+)       │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP REST / JSON / Multipart
                            ▼
┌────────────────────────────────────────────────────────┐
│           BACKEND — FastAPI + Python 3.11              │
│  - Validación estricta con Pydantic V2                 │
│  - ORM SQLAlchemy 2.0 + Motor de Hashing Bcrypt       │
│  - Generación de reportes nativos Excel (OpenPyXL)     │
│  - Puerto Host: 8000                                   │
└───────────────────────────┬────────────────────────────┘
                            │ Conexión TCP / Driver PyMySQL
                            ▼
┌────────────────────────────────────────────────────────┐
│          BASE DE DATOS — MySQL 8.0 (InnoDB)            │
│  - Juego de caracteres utf8mb4 / utf8mb4_unicode_ci    │
│  - Mapeo Dinámico Anti-XAMPP: Host 3307-3309 -> 3306   │
└────────────────────────────────────────────────────────┘
```

### 3.1 Tecnologías Principales

* **Backend**:
  * **Python 3.11**
  * **FastAPI 0.110+**: Enrutamiento asíncrono y documentación interactiva automática en Swagger (`/docs`) y ReDoc (`/redoc`).
  * **SQLAlchemy 2.0**: Mapeo relacional objeto (ORM) con gestión de transacciones y pools de conexiones.
  * **Pydantic V2**: Validación rigurosa de tipos y esquemas DTO.
  * **Passlib + Bcrypt 4.x**: Cifrado irreversible y autenticación robusta de contraseñas.
  * **PyJWT**: Generación y verificación de tokens de acceso seguros (`HS256`).
  * **OpenPyXL**: Generación nativa de hojas de cálculo binarias Excel (`.xlsx`).
  * **Holidays**: Cálculo exacto de días hábiles colombianos bajo la Ley Emiliani.

* **Frontend**:
  * **React 18**: Arquitectura basada en componentes funcionales y Hooks.
  * **Vite 5**: Entorno de desarrollo ultrarrápido y empaquetado optimizado.
  * **React Router DOM 6**: Enrutamiento protegido por roles y contexto de sesión.
  * **Axios**: Cliente HTTP con interceptores de tokens JWT.
  * **Sistema de Internacionalización (i18n)**: Soporte bilingüe completo (**Inglés por defecto**, conmutador a **Español** en tiempo de ejecución sin recargar la página).

* **Infraestructura y Aislamiento**:
  * **Docker & Docker Compose**: Configuración multiservicio orquestada.
  * **Mecanismo Anti-XAMPP**: Rango de puertos dinámico (`3307-3309:3306`) para el contenedor de base de datos, garantizando que el sistema no colisione con instalaciones locales de XAMPP, WAMP o MariaDB en el puerto 3306.
  * **Flexibilidad de Puerto Vite**: `strictPort: false` en `vite.config.js`, permitiendo salto automático a puertos contiguos (3001, 3002) si el puerto 3000 estuviese en uso.

---

## 4. Cuentas Oficiales y Credenciales de Evaluación

Todas las cuentas oficiales del sistema utilizan el dominio corporativo oficial `@docusol.com` y están configuradas con la contraseña global de evaluación:

> **Contraseña para todas las cuentas**: `Password123!`

| # | Nombre del Funcionario | Correo Corporativo | Rol | Sede Operativa |
| :-: | :--- | :--- | :--- | :--- |
| **1** | Carlos Admin | `admin@docusol.com` | Administrador | Bogotá |
| **2** | Laura Radicadora Bogotá | `radicador.bogota@docusol.com` | Radicador | Bogotá |
| **3** | Andrés Gestionador Bogotá | `gestionador.bogota@docusol.com` | Gestionador | Bogotá |
| **4** | Sofía Administradora Medellín | `admin.medellin@docusol.com` | Administrador | Medellín |
| **5** | Marta Radicadora Medellín | `radicador.medellin@docusol.com` | Radicador | Medellín |
| **6** | Felipe Gestionador Medellín | `gestionador.medellin@docusol.com` | Gestionador | Medellín |
| **7** | Julián Administrador Cali | `admin.cali@docusol.com` | Administrador | Cali |
| **8** | Diana Radicadora Cali | `radicador.cali@docusol.com` | Radicador | Cali |
| **9** | Santiago Gestionador Cali | `gestionador.cali@docusol.com` | Gestionador | Cali |

---

## 5. Mapeo Detallado de Historias de Usuario (HU-001 a HU-010)

### HU-001: Autenticación de Usuario y Control de Acceso
* **Propósito**: Permitir el ingreso seguro de funcionarios a su respectiva sede operativa mediante credenciales corporativas, entregando un token JWT firmado.
* **Componentes Frontend**:
  * `src/pages/SeleccionSede.jsx` (Ruta: `/`)
  * `src/pages/Login.jsx` (Ruta: `/login/:sedeSlug`)
  * `src/contexts/AuthContext.jsx`
* **Endpoints Backend**:
  * `POST /api/auth/login` (`backend/app/routers/auth.py`)
  * `POST /token` (OAuth2 compatible form-data/json)
* **Criterios de Aceptación Cubiertos**:
  * Verificación de contraseña mediante hash Bcrypt auténtico.
  * Emisión de token JWT con tiempo de expiración y payload de `email`, `rol` y `sede`.
  * Validación perimetral por sede: el sistema bloquea con `HTTP 403` a usuarios que intenten iniciar sesión en una sede distinta a la asignada.
  * Bloqueo con `HTTP 401` y mensaje estándar ante contraseñas inválidas o usuarios inexistentes.

---

### HU-002: Gestión de Cuentas de Usuario y Roles
* **Propósito**: Proporcionar al Administrador un panel para registrar funcionarios, consultar la nómina operativa y asignar perfiles funcionales.
* **Componentes Frontend**:
  * `src/pages/DashboardAdmin.jsx` (Ruta: `/dashboard-admin`)
  * `src/pages/UsuariosAdmin.jsx` (Ruta: `/usuarios-admin`)
  * `src/pages/CrearCuentaSede.jsx` (Ruta: `/registro/:sedeSlug`)
* **Endpoints Backend**:
  * `GET /api/usuarios` (`backend/app/routers/usuarios.py`)
  * `POST /api/usuarios` (`backend/app/routers/usuarios.py`)
  * `POST /api/usuarios/registro/{sede_slug}` (`backend/app/routers/usuarios.py`)
* **Criterios de Aceptación Cubiertos**:
  * Acceso restringido exclusivamente a usuarios con rol `Administrador`.
  * Validación de unicidad de correo institucional en `tbl_usuarios` (retorna `HTTP 400` ante duplicados).
  * Asignación obligatoria de nombre, correo `@docusol.com`, rol (`Administrador`, `Radicador`, `Gestionador`) y sede (`Bogotá`, `Medellín`, `Cali`).
  * Estado inicial activo (`usr_estado = 'ACTIVO'`) y hasheo automático de contraseña inicial.

---

### HU-003: Radicación de Documentos e Indización de Metadatos
* **Propósito**: Permitir al Radicador registrar formalmente solicitudes y documentos de entrada, generando un número de radicado consecutivo y calculando el plazo legal de respuesta.
* **Componentes Frontend**:
  * `src/pages/RadicacionEntrada.jsx` (Ruta: `/radicacion-entrada`)
* **Endpoints Backend**:
  * `POST /api/radicados` (`backend/app/routers/radicados.py`)
  * `GET /api/radicados` (`backend/app/routers/radicados.py`)
* **Criterios de Aceptación Cubiertos**:
  * Generación de código de radicado único estandarizado (`RAD-2026-XXXXX`).
  * Registro de campos obligatorios: remitente, asunto, tipo de documento y sede de destino.
  * **Cálculo de Término Legal Colombiano (SLA)**: Adición automática de 5 días hábiles a la fecha de radicación, excluyendo fines de semana y días festivos nacionales de Colombia (Ley Emiliani).
  * Estado inicial automático. Si la `sede de destino` es distinta a la del operador, el expediente queda **en la sede de destino** con estado `TRASLADADO` y espera la aceptación formal de su gestionador (HU-006); si coincide, queda `RADICADO` en la propia sede. Esto aplica el *"enrutamiento inicial hacia la sede de destino"* del Perfil Radicador de la Propuesta Comercial, y es lo que da sentido al estado `TRASLADADO` y a la bandeja de recepción de HU-006. El campo `rad_sede_origen` conserva la sede desde la que se radicó.
  * El traslado de HU-005 cubre los reasignamientos posteriores, una vez que el expediente ya está en la sede destino.

---

### HU-004: Carga y Asociación de Adjuntos Digitales
* **Propósito**: Asociar el documento físico digitalizado al radicado para consulta en línea por los funcionarios involucrados.
* **Componentes Frontend**:
  * `src/pages/CargarAnexos.jsx` (Ruta: `/cargar-anexos`)
* **Endpoints Backend**:
  * `POST /api/anexos/upload` (`backend/app/routers/anexos.py`)
  * `GET /api/anexos/{rad_id}` (`backend/app/routers/anexos.py`)
  * `GET /api/anexos/download/{anexo_id}` (`backend/app/routers/anexos.py`)
* **Criterios de Aceptación Cubiertos**:
  * Restricción estricta de tipo MIME: solo se aceptan documentos en formato **PDF** (`HTTP 400` ante otros formatos).
  * Restricción estricta de tamaño: tamaño máximo de **15 MB** por archivo.
  * Almacenamiento seguro en disco con nombres sanitizados para prevenir colisiones.
  * Registro transaccional en `tbl_anexos` vinculado a `anx_rad_id`.

---

### HU-005: Reasignación y Traslado Inter-Sedes
* **Propósito**: Transferir formalmente la responsabilidad de gestión de un expediente radicado hacia otra sede operativa.
* **Componentes Frontend**:
  * `src/pages/TrasladoSede.jsx` (Ruta: `/traslado-sede`)
* **Endpoints Backend**:
  * `POST /api/traslados` (`backend/app/routers/traslados.py`)
  * `GET /api/traslados/radicados-disponibles` (`backend/app/routers/traslados.py`)
* **Criterios de Aceptación Cubiertos**:
  * Solo se pueden trasladar radicados ubicados en la sede operativa del usuario en sesión.
  * Prohibición de auto-traslado a la misma sede de origen.
  * Campo obligatorio de justificación o motivo institucional del traslado (`HTTP 400` si está vacío).
  * Actualización del estado del expediente a `TRASLADADO` y registro en `tbl_historial_traslados`.

---

### HU-006: Recepción y Aceptación de Expedientes Trasladados
* **Propósito**: Bandeja de entrada para que los Gestionadores de la sede destino inspeccionen y acepten formalmente los expedientes que les fueron remitidos.
* **Componentes Frontend**:
  * `src/pages/BandejaRecepcion.jsx` (Ruta: `/bandeja-recepcion`)
* **Endpoints Backend**:
  * `GET /api/recepcion/pendientes` (`backend/app/routers/recepcion.py`)
  * `POST /api/recepcion/aceptar/{rad_id}` (`backend/app/routers/recepcion.py`)
  * `POST /api/recepcion/aceptar` (alias con `rad_id` en el cuerpo, `backend/app/routers/recepcion.py`)
* **Criterios de Aceptación Cubiertos**:
  * Filtrado por sede: la bandeja muestra los expedientes pendientes de la sede del usuario. Incluye los `TRASLADADO` desde otra sede **y** los `RADICADO` en la propia sede, que también están pendientes de trámite.
  * Bloqueo si un usuario de otra sede intenta forzar la aceptación. Se responde `404` y no `403`, de forma coherente con el resto de módulos (`radicados.py`, `anexos.py`, `cierre.py`), para no revelar la existencia de expedientes de otras sedes.
  * Al pulsar el botón de aceptar, el estado cambia a `ACEPTADO`, el expediente pasa a la pestaña "En Gestión" del Gestionador y se crea el registro en `tbl_historial_aceptaciones` con usuario, fecha, hora, sede **e IP de origen**.

---

### HU-007: Cierre y Finalización de Trámite Documental
* **Propósito**: Culminar formalmente el trámite de un expediente aceptado, anexando obligatoriamente el oficio de respuesta y las observaciones finales.
* **Componentes Frontend**:
  * `src/pages/CierreExpediente.jsx` (Ruta: `/cierre-expediente`)
* **Endpoints Backend**:
  * `POST /api/cierre` (`backend/app/routers/cierre.py`)
  * `GET /api/cierre/radicados-gestion` (`backend/app/routers/cierre.py`)
* **Criterios de Aceptación Cubiertos**:
  * Obligatoriedad del archivo PDF de respuesta final y de las observaciones de cierre (`HTTP 400` si faltan).
  * Permite la finalización por parte del Gestionador de la sede o por el Administrador. El Administrador puede cerrar expedientes de cualquier sede en ejercicio de los *"permisos operacionales de respaldo"* de la Propuesta Comercial; si la cobertura fuera solo de su propia sede, un gestor ausente en Bogotá dejaría expedientes sin poder finalizar.
  * Transición de estado a `FINALIZADO`.
  * Almacenamiento en `tbl_respuestas` y en `tbl_historial_cierres` guardando el identificador real del usuario que cerró el trámite.

---

### HU-008: Consulta de Trazabilidad e Historial Inalterable
* **Propósito**: Ofrecer una bitácora forense y cronológica completa de todas las etapas, eventos, actores y estados por los que ha transitado un radicado.
* **Componentes Frontend**:
  * `src/pages/AuditoriaTrazabilidad.jsx` (Ruta: `/auditoria-trazabilidad`)
* **Endpoints Backend**:
  * `GET /api/auditoria/{codigo_radicado}` (`backend/app/routers/auditoria.py`)
* **Criterios de Aceptación Cubiertos**:
  * Búsqueda por código de radicado exacto (`HTTP 404` con mensaje descriptivo si no existe).
  * Consulta transversal permitida para Administradores de cualquier sede.
  * Reconstrucción cronológica ascendente unificada (Radicación original -> Carga de anexos -> Traslados inter-sedes -> Aceptaciones -> Cierre de expediente).

---

### HU-009: Generación y Exportación de Reportes Parametrizados
* **Propósito**: Panel gerencial para consultar expedientes con filtros combinados y descargar los datos tabulares en formato Microsoft Excel nativo.
* **Componentes Frontend**:
  * `src/pages/ReportesParametrizados.jsx` (Ruta: `/reportes-parametrizados`)
* **Endpoints Backend**:
  * `GET /api/reportes/parametrizados` (`backend/app/routers/reportes.py`)
  * `GET /api/reportes/exportar-excel` (`backend/app/routers/reportes.py`)
* **Criterios de Aceptación Cubiertos**:
  * Filtrado multidimensional por: rango de fechas (desde/hasta), sede operativa y estado (`RADICADO`, `TRASLADADO`, `ACEPTADO`, `FINALIZADO`).
  * Validación de coherencia de fechas: rechaza con `HTTP 400` si la fecha final es anterior a la fecha inicial.
  * Exportación binaria directa a `.xlsx` utilizando `openpyxl` con encabezados de columna corporativos y estilos aplicados.

---

### HU-010: Dashboard de Alertas y Vencimientos Legales (Semáforo SLA)
* **Propósito**: Panel de control visual con clasificación semafórica en tiempo real de los expedientes según su tiempo restante de atención.
* **Componentes Frontend**:
  * `src/pages/DashboardVencimientos.jsx` (Ruta: `/dashboard-vencimientos`)
* **Endpoints Backend**:
  * `GET /api/dashboard/vencimientos` (`backend/app/routers/dashboard.py`)
* **Criterios de Aceptación Cubiertos**:
  * **Tarjetas KPI Consolidadas**:
    * 🔴 **CRÍTICO**: Menos de 24 horas restantes o término ya vencido.
    * 🟡 **ATENCIÓN**: Entre 24 y 72 horas restantes.
    * 🟢 **EN TIEMPO**: Más de 72 horas restantes.
  * Segmentación por rol: los Gestionadores ven únicamente sus casos asignados; los Administradores supervisan todos los casos de su jurisdicción.
  * Acceso directo desde la tabla interactiva hacia el formulario de cierre (`HU-007`).

---

## 6. Guía de Instalación y Despliegue con Docker

### Requisitos Previos
* **Docker Desktop** (con Docker Compose v2+) instalado y en ejecución en Windows, Linux o macOS.
* Puertos libres recomendados: `3000` (frontend), `8000` (backend), `3307` a `3309` (MySQL Anti-XAMPP).

---

### Paso 1: Clonar el Repositorio e Ingresar a la Carpeta
```bash
git clone <url-del-repositorio>
cd "Gestion Documental"
```

---

### Paso 2: Levantar el Entorno Completo con Docker Compose
Ejecute el siguiente comando para compilar las imágenes e iniciar los contenedores en segundo plano:

```bash
docker compose up -d --build
```

El orquestador iniciará 3 servicios:
1. `nextgen_mysql`: Base de datos MySQL 8.0 en la red interna (puerto host `3307-3309`).
2. `nextgen_backend`: API FastAPI en Python 3.11 (puerto host `8000`).
3. `nextgen_frontend`: Servidor web Vite + React 18 (puerto host `3000`).

---

### Paso 3: Sincronización Automática de Contraseñas (Bcrypt)
Para garantizar que todos los usuarios semilla cuenten con hashes Bcrypt auténticos y el dominio corporativo `@docusol.com`, ejecute el script de sincronización dentro del contenedor backend:

```bash
docker exec -it nextgen_backend python sync_passwords.py
```

*Salida esperada:*
```text
======================================================================
 DocuSol — Sincronización de Contraseñas de Evaluación (Bcrypt)
======================================================================
[*] Contraseña genérica de evaluación: Password123!
[+] Conexión a la base de datos establecida exitosamente.
[*] Generando hash Bcrypt con esquema passlib...
[+] Hash generado: $2b$12$...
[+] Verificación interna de Bcrypt: OK.
  [ACTUALIZADO] Administrador  | admin@docusol.com              | Sede: Bogotá
  [ACTUALIZADO] Radicador      | radicador.bogota@docusol.com   | Sede: Bogotá
  ...
[✓] Éxito: 9 usuarios actualizados, 0 usuarios creados.
[✓] Todas las cuentas están configuradas con contraseña: 'Password123!'
======================================================================
```

---

### Paso 4: Ejecución del Script de Validación de Usuarios
Valide de forma exhaustiva el funcionamiento del login, JWT y Bcrypt para las 3 sedes ejecutando el script oficial:

```bash
docker exec -it nextgen_backend python tests/validar_usuarios.py
```

*Salida esperada:*
```text
========================================================================================
 DocuSol (Soluciones en Documentación) — Validación Automatizada de Usuarios y Roles
========================================================================================
[*] Contraseña evaluada : Password123!
[*] Total usuarios     : 7
[*] Algoritmo Hashing  : Bcrypt (passlib)
[*] Algoritmo Tokens   : JWT HS256 (PyJWT)
========================================================================================
 #  | ROL            | SEDE     | CORREO                           | STATUS | JWT  | BCRYPT
----------------------------------------------------------------------------------------
  1 | Administrador  | Bogotá   | admin@docusol.com                | 200 OK | OK   | OK
  2 | Radicador      | Bogotá   | radicador.bogota@docusol.com     | 200 OK | OK   | OK
  3 | Gestionador    | Bogotá   | gestionador.bogota@docusol.com   | 200 OK | OK   | OK
  4 | Radicador      | Medellín | radicador.medellin@docusol.com   | 200 OK | OK   | OK
  5 | Gestionador    | Medellín | gestionador.medellin@docusol.com | 200 OK | OK   | OK
  6 | Radicador      | Cali     | radicador.cali@docusol.com       | 200 OK | OK   | OK
  7 | Gestionador    | Cali     | gestionador.cali@docusol.com     | 200 OK | OK   | OK
----------------------------------------------------------------------------------------
[*] Ejecutando validaciones de seguridad negativa...
    - Bloqueo de contraseña inválida (HTTP 401): [OK]
    - Bloqueo de sede cruzada (HTTP 403)       : [OK]
========================================================================================
[OK] RESULTADO: TODOS LOS 7 USUARIOS VALIDADOS EXITOSAMENTE
========================================================================================
```

---

### Paso 5: Acceso a la Aplicación Web
Abra su navegador web e ingrese a las siguientes URLs:

* **Aplicación Web Principal (Frontend)**: [http://localhost:3000](http://localhost:3000)
* **Documentación Interactiva de la API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Documentación Técnica de la API (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 7. Ejecución de Pruebas Automatizadas con Pytest

El proyecto cuenta con tres niveles de prueba, complementarios entre sí.

| Nivel | Script | Qué valida |
| :--- | :--- | :--- |
| Unitarias e integración | `tests/test_sprint1_sprint2.py` | Criterios de aceptación de Sprint 1 y Sprint 2 sobre la base de datos |
| Extremo a extremo | `e2e_10hu.py` | Flujo completo de las 10 historias de usuario contra la API en ejecución |
| Conformidad documental | `tests/test_conformidad_readme.py` | Que el comportamiento real coincida, criterio por criterio, con lo que este README y la Propuesta Comercial exigen |

Para ejecutar la suite unitaria dentro del contenedor backend:

```bash
docker exec -it nextgen_backend pytest tests/test_sprint1_sprint2.py -v
```

O en un entorno Python local (requiere dependencias de `requirements.txt` instaladas):
```bash
python -m pytest backend/tests/test_sprint1_sprint2.py -v
```

*Resultado de ejecución:*
```text
========================= 54 passed, 0 failed in 36.56s =========================
```

### 7.1 Pruebas de extremo a extremo

Recorre el ciclo de vida completo de un expediente: radicación, carga de
anexos, traslado inter-sedes, aceptación, cierre, auditoría y reportes.

```bash
docker exec -it nextgen_backend python e2e_10hu.py http://localhost:8000
```

```text
Total verificaciones : 106
Correctas            : 106
Fallidas             : 0
```

### 7.2 Verificación de conformidad con el README

Este script cita la línea del README que exige cada comportamiento y la contrasta
contra la API real. Es el que permite afirmar que la entrega cumple de forma
literal la especificación, y no solo las pruebas escritas para el código.

```bash
docker exec -it nextgen_backend python tests/test_conformidad_readme.py
```

```text
Cumple: 14 | No cumple: 0 | Total: 14
```

Entre sus comprobaciones destacadas están:

* **Ley Emiliani**: recalca 540 plazos legales con una implementación independiente
  y los contrasta con `app/utils/business_days.py`; además verifica de forma
  explícita que un festivo que cae en domingo se traslada al lunes y ese lunes
  **no** se descuenta del término.
* **Matriz de roles**: comprueba el acceso esperado y el denegado para cada rol
  en HU-005, HU-008 y HU-010.
* **Aislamiento entre sedes**: comprueba que un usuario de otra sede no acepta
  ni cierra expedientes ajenos.
* **Dominio corporativo**: comprueba que `@docusol.com` se acepta y que
  cualquier otro dominio se rechaza con `HTTP 400`.

---

## 8. Diagnóstico y Solución de Problemas (Troubleshooting)

### A. Conflicto con XAMPP / MariaDB en el puerto 3306
* **Causa**: XAMPP o un servicio MySQL local está ocupando el puerto estándar `3306` en Windows.
* **Solución**: DocuSol incluye aislamiento dinámico en `docker-compose.yml` (`"${DB_PORT_EXTERNAL:-3307-3309}:3306"`). El contenedor de base de datos se enlaza automáticamente a `3307` (o `3308`/`3309`). No es necesario detener XAMPP.

### B. El frontend no carga en el puerto 3000
* **Causa**: Otro proceso local ocupa el puerto 3000.
* **Solución**: Vite está configurado con `strictPort: false`. El servidor saltará automáticamente a `http://localhost:3001` o `3002`. Revise los logs con `docker logs nextgen_frontend` para verificar la URL exacta.

### C. Error 401 "Credenciales de acceso no válidas"
* **Causa**: El contenedor MySQL ya existía de una ejecución previa con contraseñas antiguas.
* **Solución**: Ejecute `docker exec -it nextgen_backend python sync_passwords.py` para forzar la actualización de hashes Bcrypt de todas las cuentas al estándar `Password123!`.

### D. Verificación de Logs en Tiempo Real
```bash
# Ver logs del backend
docker logs -f nextgen_backend

# Ver logs de la base de datos
docker logs -f nextgen_mysql

# Ver logs del frontend
docker logs -f nextgen_frontend
```

---

## 9. Licencia y Créditos Corporativos

**DocuSol V1.1** — Sistema de Gestión Documental.  
Desarrollado conforme a los requerimientos de arquitectura limpia, seguridad perimetral, trazabilidad legal y estándares de internacionalización.  
Todos los derechos reservados © 2026.
