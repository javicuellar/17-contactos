# Documentación Técnica — Gestión de Contactos

## Descripción general

Aplicación web de gestión de contactos personales construida con Flask. Permite a múltiples usuarios gestionar sus propios contactos (personas), clasificarlos mediante etiquetas e importarlos masivamente desde ficheros CSV exportados por Google Contacts. Implementa baja lógica (soft delete) y auditoría completa en las entidades principales.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Framework web | Flask |
| ORM | Flask-SQLAlchemy (SQLAlchemy) |
| Base de datos | SQLite |
| Autenticación | Flask-Login |
| Formularios | Flask-WTF / WTForms |
| UI | Flask-Bootstrap (Bootstrap 5) |
| Procesamiento CSV | pandas |
| Hashing de contraseñas | Werkzeug security |
| Internacionalización | Babel (locale forzado a `es`) |

---

## Estructura del proyecto

```
run.py                          # Punto de entrada
app/
├── __init__.py
├── app.py                      # Factory: Flask, SQLAlchemy, LoginManager, Blueprints
├── config.py                   # Configuración desde variables de entorno
├── comunes/
│   └── utilidades.py           # Procesamiento de CSV de Google Contacts
├── contactos/
│   ├── __init__.py             # Blueprint: contactos_bp
│   ├── models.py               # Modelos: Personas, Rel_persona_etiqueta
│   ├── forms.py                # Formularios: formContacto, formImportar, formSINO
│   └── routes.py               # Rutas CRUD + importación
├── etiquetas/
│   ├── __init__.py             # Blueprint: etiquetas_bp
│   ├── models.py               # Modelo: Etiquetas
│   ├── forms.py                # Formularios: formEtiqueta, formSINO
│   └── routes.py               # Rutas CRUD (solo admin)
├── usuarios/
│   ├── __init__.py             # Blueprint: usuarios_bp
│   ├── models.py               # Modelo: Usuarios (Flask-Login)
│   ├── forms.py                # Formularios: LoginForm, formUsuario, formChangePassword
│   └── routes.py               # Login, logout, registro, gestión de usuarios
└── templates/
    ├── base.html
    ├── contactos/
    ├── etiquetas/
    └── usuarios/
```

---

## Configuración (`app/config.py`)

Todos los parámetros sensibles se leen desde variables de entorno:

| Variable de entorno | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave secreta Flask (CSRF, sesiones) | — (obligatoria) |
| `DEBUG` | Modo depuración Flask | — |
| `APP_PORT_CONTACTOS` | Puerto de escucha | — |
| `RUTA_BD_CONTACTOS` | Ruta absoluta al fichero SQLite | `./instancias/contactos.db` |

Locale forzado a `es` / `Europe/Madrid` mediante `BABEL_DEFAULT_LOCALE` y `BABEL_DEFAULT_TIMEZONE`.

---

## Modelos de datos

### `Usuarios` (`usuarios`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | Integer | PK |
| `username` | String(100) | NOT NULL |
| `password_hash` | String(128) | NOT NULL |
| `nombre` | String(200) | NOT NULL |
| `email` | String(200) | NOT NULL |
| `admin` | Boolean | Default False |

Implementa la interfaz de Flask-Login (`is_authenticated`, `is_active`, `is_anonymous`, `get_id`). El campo `password` es una propiedad write-only que almacena el hash generado por `werkzeug.security.generate_password_hash`.

---

### `Personas` (`personas`)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer | PK |
| `UsuarioId` | Integer FK → `usuarios.id` | Propietario del contacto |
| `nombre` | String(150) | NOT NULL |
| `notas` | String(255) | Texto libre |
| `usuario_alta` | String(100) | Auditoría: quién creó |
| `fecha_alta` | DateTime | Auditoría: cuándo creó |
| `usuario_mod` | String(100) | Auditoría: quién modificó |
| `fecha_mod` | DateTime | Auditoría: cuándo modificó |
| `usuario_baja` | String(100) | Auditoría: quién dio de baja |
| `fecha_baja` | DateTime | NULL = activo; NOT NULL = baja lógica |

Relación `one-to-many` con `Rel_persona_etiqueta` con `cascade="all, delete-orphan"`.

---

### `Etiquetas` (`etiquetas`)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer | PK |
| `nombre` | String(100) | Nombre de la etiqueta |
| `descripcion` | String(255) | Descripción |

Las etiquetas son globales (no pertenecen a ningún usuario). Solo los administradores pueden crearlas, editarlas o eliminarlas.

---

### `Rel_persona_etiqueta` (`rel_persona_etiqueta`)

Tabla de asociación M:N entre `Personas` y `Etiquetas`, con auditoría y baja lógica propias.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer | PK |
| `EtiquetaId` | Integer FK → `etiquetas.id` | |
| `PersonaId` | Integer FK → `personas.id` | |
| `usuario_alta` | String(100) | |
| `fecha_alta` | DateTime | |
| `usuario_mod` | String(100) | |
| `fecha_mod` | DateTime | |
| `usuario_baja` | String(100) | |
| `fecha_baja` | DateTime | NULL = relación activa |

---

## Diagrama entidad-relación (simplificado)

```
Usuarios (1) ──────────── (N) Personas
                                  │
                                  │ (N)
                          Rel_persona_etiqueta
                                  │
                                  │ (N)
                              Etiquetas (1)
```

---

## Rutas y controladores

### Autenticación (`usuarios/routes.py`)

| Método | Ruta | Función | Acceso |
|---|---|---|---|
| GET / POST | `/` o `/login` | `login()` | Público |
| GET | `/logout` | `logout()` | Autenticado |
| GET / POST | `/registro` | `registro()` | Público |
| POST | `/perfil/editar` | `perfil_editar()` | Autenticado |
| GET | `/usuarios/` | `usuarios_list()` | Admin |
| POST | `/usuarios/new` | `usuarios_new()` | Admin |
| POST | `/usuarios/<uid>/edit` | `usuarios_edit()` | Admin |
| POST | `/usuarios/<uid>/delete` | `usuarios_delete()` | Admin |

---

### Contactos (`contactos/routes.py`)

| Método | Ruta | Función | Descripción |
|---|---|---|---|
| GET | `/contactos/` | `contactos()` | Lista filtrada por usuario, nombre y etiqueta |
| POST | `/contactos/new` | `contactos_new()` | Crear persona + asignar etiquetas |
| POST | `/contactos/<id>/edit` | `contactos_edit()` | Editar persona + reemplazar etiquetas |
| POST | `/contactos/<id>/delete` | `contactos_delete()` | Baja lógica de persona y sus relaciones |
| GET / POST | `/importar` | `importar()` | Importación masiva desde CSV |

**Filtrado en lista:** La ruta `/contactos/` acepta query params `nombre` y `etiqueta_id`. El filtro por nombre aplica normalización Unicode (sin tildes, minúsculas) mediante la función auxiliar `sin_tildes()`.

**Aislamiento por usuario:** Todas las consultas filtran por `UsuarioId=current_user.id`. Un usuario no puede ver ni modificar los contactos de otro salvo que sea administrador.

---

### Etiquetas (`etiquetas/routes.py`)

| Método | Ruta | Función | Acceso |
|---|---|---|---|
| GET | `/etiquetas/` | `etiquetas()` | Autenticado |
| GET / POST | `/etiqueta/new` | `etiqueta_edit()` | Admin |
| GET / POST | `/etiqueta/<id>/edit` | `etiqueta_edit()` | Admin |
| GET / POST | `/etiqueta/<id>/delete` | `etiqueta_delete()` | Admin |

---

## Baja lógica (soft delete)

Las entidades `Personas` y `Rel_persona_etiqueta` no se eliminan físicamente. Al dar de baja se rellena `fecha_baja` + `usuario_baja`. Todas las consultas de datos activos incluyen el filtro:

```python
.filter(Personas.fecha_baja == None)
.filter(Rel_persona_etiqueta.fecha_baja == None)
```

Al editar etiquetas de un contacto se da de baja lógica el conjunto de relaciones anterior y se crean nuevas relaciones activas.

---

## Importación CSV (`comunes/utilidades.py`)

La función `procesar_archivo(archivo)` lee un CSV exportado desde Google Contacts y lo transforma en una lista de diccionarios normalizados.

**Mapeos implementados:**

- `transf`: columnas de valor único (`First Name`, `Last Name`, `Notes`, `Birthday`, etc.)
- `doble`: columnas con pares Label/Value (`Phone`, `E-mail`, `Address`, `Website`, etc.)
- `labels`: normalización de etiquetas de tipo (`Work`, `Mobile`, `Home`, etc.)
- `etiquetas`: lista configurable de etiquetas de Google a importar como etiquetas de la aplicación

**Lógica de importación en `contactos/routes.py` → `importar()`:**

1. Leer CSV con `procesar_archivo`.
2. Para cada entrada: buscar persona existente del usuario por nombre exacto.
3. Si no existe → crear nueva (`Personas`).
4. Si existe → actualizar notas, dar baja lógica a etiquetas anteriores.
5. Para cada etiqueta del CSV: buscar o crear `Etiquetas`, crear `Rel_persona_etiqueta`.
6. Devolver resumen: `nuevos`, `actualizados`, `errores`.

---

## Seguridad

- **CSRF:** Flask-WTF activo globalmente. Se inyecta `csrf_token` como función de contexto Jinja2 para que esté disponible en templates incluidos con `{% include %}`.
- **Contraseñas:** Almacenadas como hash con `werkzeug.security` (PBKDF2/SHA256).
- **Autenticación:** Flask-Login protege todas las rutas con `@login_required`.
- **Autorización:** Las rutas de administración verifican `current_user.is_admin()` y devuelven 403/404 en caso de acceso no autorizado. Las operaciones sobre contactos verifican que `p.UsuarioId == current_user.id`.
- **HTTPS:** El código incluye configuración comentada para TLS directo y para proxy inverso (modo producción recomendado).

---

## Arranque de la aplicación (`run.py`)

```python
with aplicacion.app_context():
    db.create_all()   # Crea las tablas si no existen
aplicacion.run(port=APP_PORT_CONTACTOS)
```

El puerto se lee de la variable de entorno `APP_PORT_CONTACTOS`. Las tablas se crean automáticamente si la base de datos es nueva.

---

## Notas de implementación relevantes

- Los Blueprints (`usuarios_bp`, `contactos_bp`, `etiquetas_bp`) se registran en `app/app.py` pero las rutas están definidas directamente sobre la instancia global `app`, no sobre el Blueprint. Esto es funcionalmente equivalente pero rompe el encapsulamiento estándar de Blueprint.
- `etiquetas/routes.py` referencia `Rel_contacto_etiqueta` (nombre anterior del modelo) en lugar de `Rel_persona_etiqueta`. Esto causará un `ImportError` en tiempo de ejecución al acceder a las rutas de etiquetas. El modelo correcto es `Rel_persona_etiqueta`.
- La lista `etiquetas` en `utilidades.py` está codificada en duro con valores específicos de un entorno concreto. Se debería externalizar a configuración o base de datos para que sea reutilizable.
- `formContacto` en `contactos/forms.py` define un campo `apellidos` que no existe en el modelo `Personas` ni se usa en las rutas.
