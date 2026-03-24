# Gestión de Contactos

Aplicación web para organizar tus contactos personales. Puedes añadir personas, clasificarlas con etiquetas e importar contactos directamente desde Google Contacts.

---

## Requisitos previos

- Python 3.12 o superior
- pip

---

## Instalación

**1. Clona o descomprime el proyecto:**

```bash
unzip 17-contactos.zip
cd app
```

**2. Crea un entorno virtual e instala las dependencias:**

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

pip install flask flask-login flask-sqlalchemy flask-bootstrap flask-wtf pandas
```

**3. Configura las variables de entorno:**

Crea un fichero `.env` en la raíz del proyecto o expórtalas en tu terminal:

```bash
export SECRET_KEY="una-clave-secreta-larga-y-aleatoria"
export APP_PORT_CONTACTOS=5000
export DEBUG=True

# Opcional: ruta personalizada para la base de datos
# export RUTA_BD_CONTACTOS=/ruta/a/mi/contactos.db
```

**4. Arranca la aplicación:**

```bash
python run.py
```

La primera vez, la aplicación crea automáticamente la base de datos SQLite en `instancias/contactos.db`.

Abre el navegador en: **http://localhost:5000**

---

## Primer uso

### Crear una cuenta

Ve a **http://localhost:5000/registro**, rellena tu nombre de usuario, contraseña y datos de perfil y pulsa *Aceptar*.

> El primer usuario registrado tendrá que ser promocionado a administrador directamente en la base de datos si se quiere gestionar etiquetas y usuarios. Los siguientes usuarios pueden crearse desde el panel de administración.

### Iniciar sesión

Introduce tu nombre de usuario y contraseña en la pantalla de login.

---

## Funcionalidades principales

### Contactos

Desde la pantalla principal (`/contactos/`) puedes:

- **Ver** todos tus contactos ordenados alfabéticamente.
- **Buscar** por nombre usando el campo de búsqueda (acepta búsquedas sin tildes).
- **Filtrar** por etiqueta usando el desplegable.
- **Añadir** un contacto nuevo con el botón *Nuevo contacto*.
- **Editar** un contacto existente pulsando el icono de lápiz.
- **Eliminar** un contacto pulsando el icono de papelera (se pedirá confirmación).

Al crear o editar un contacto puedes asignarle una o varias etiquetas manteniendo pulsada la tecla `Ctrl` (o `Cmd` en macOS) mientras haces clic en el listado de etiquetas.

---

### Importar contactos desde Google Contacts

1. En Google Contacts, selecciona los contactos que quieres exportar y elige **Exportar → Google CSV**.
2. En la aplicación, ve al menú y selecciona **Importar**.
3. Selecciona el fichero CSV descargado y pulsa **Importar**.

La aplicación mostrará un resumen con el número de contactos nuevos, actualizados y los posibles errores.

> **Nota:** Solo se importan las etiquetas que estén configuradas en la aplicación. Consulta con el administrador si necesitas añadir nuevas etiquetas de importación.

---

### Etiquetas *(solo administradores)*

Las etiquetas son categorías globales que todos los usuarios pueden asignar a sus contactos.

Desde `/etiquetas/` un administrador puede:

- **Ver** todas las etiquetas existentes con su descripción.
- **Buscar** por nombre o descripción.
- **Crear** una nueva etiqueta con el botón *Nueva etiqueta*.
- **Editar** el nombre o la descripción de una etiqueta.
- **Eliminar** una etiqueta (se mostrará cuántos contactos la tienen asignada).

---

### Gestión de usuarios *(solo administradores)*

Desde `/usuarios/` un administrador puede:

- **Ver** todos los usuarios registrados.
- **Buscar** por nombre de usuario o nombre completo.
- **Crear** nuevos usuarios con o sin permisos de administrador.
- **Editar** los datos de cualquier usuario (incluida la contraseña).
- **Eliminar** usuarios (no es posible eliminar el propio usuario).

---

### Editar tu perfil

Haz clic en tu nombre de usuario en la barra superior para abrir el panel de perfil. Desde ahí puedes cambiar tu nombre, email y contraseña.

---

## Seguridad y privacidad

- Cada usuario solo puede ver y gestionar sus propios contactos.
- Las contraseñas se almacenan cifradas y nunca en texto plano.
- Todas las operaciones están protegidas frente a ataques CSRF.
- Los contactos eliminados no se borran de la base de datos (baja lógica), lo que permite auditoría de cambios.

---

## Estructura de la base de datos

La aplicación utiliza una base de datos SQLite local. El fichero se crea automáticamente en `instancias/contactos.db` al arrancar por primera vez.

---

## Producción

Para entornos de producción se recomienda:

- Usar un proxy inverso (nginx, Caddy) en lugar de exponer Flask directamente.
- Configurar HTTPS a nivel del proxy inverso.
- Asegurarse de que `DEBUG=False` y `SECRET_KEY` tiene un valor seguro y aleatorio.
- Hacer copias de seguridad periódicas del fichero `contactos.db`.

---

## Solución de problemas frecuentes

**La aplicación no arranca:**
Verifica que `SECRET_KEY` y `APP_PORT_CONTACTOS` están definidas como variables de entorno.

**Error al importar CSV:**
Asegúrate de que el fichero es un CSV exportado desde Google Contacts con la opción *Google CSV* (no vCard).

**No puedo crear etiquetas:**
La gestión de etiquetas requiere permisos de administrador. Contacta con el administrador de la aplicación.

**He olvidado mi contraseña:**
Un administrador puede cambiar tu contraseña desde el panel de gestión de usuarios (`/usuarios/`).
