# Gestión de Contactos

Aplicación web Flask para organizar contactos personales. Permite gestionar personas, datos de contacto, eventos, relaciones y etiquetas, además de importar contactos exportados desde Google Contacts.

## Requisitos

- Python 3.12 o superior (la imagen Docker incluida usa Python 3.14).
- `pip`.
- Un navegador web.

La aplicación utiliza SQLite, por lo que no necesita un servidor de base de datos adicional.

## Instalación local

Los comandos siguientes deben ejecutarse desde la raíz del proyecto, donde están `run.py` y `requirements.txt`.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell impide activar el entorno por la política de ejecución, se puede ejecutar `\.venv\Scripts\python.exe` directamente o habilitar la política para el usuario actual.

### Linux y macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuración

La configuración se realiza mediante variables de entorno. `SECRET_KEY` es necesaria para las sesiones y la protección CSRF.

### PowerShell

```powershell
$env:SECRET_KEY = "una-clave-secreta-larga-y-aleatoria"
$env:APP_PORT_CONTACTOS = "5000"
$env:DEBUG = "False"
```

### Linux y macOS

```bash
export SECRET_KEY="una-clave-secreta-larga-y-aleatoria"
export APP_PORT_CONTACTOS=5000
export DEBUG=False
```

Variables disponibles:

```text
VARIABLE              OBLIGATORIA  VALOR PREDETERMINADO  DESCRIPCIÓN
SECRET_KEY             Sí           Sin valor             Clave secreta de Flask, sesiones y CSRF.
APP_PORT_CONTACTOS     No           5000                  Puerto HTTP de la aplicación.
DEBUG                  No           Sin valor             Valor de depuración. En producción debe ser False.
RUTA_BD_CONTACTOS      No           data/contactos.db     Ruta del fichero SQLite.
```

La configuración no carga automáticamente un fichero `.env` en una ejecución local. Si se usa uno, hay que exportar sus variables con la herramienta elegida o definirlas en el entorno de ejecución.

## Cómo ejecutar

Con el entorno virtual activado y las variables configuradas:

```bash
python run.py
```

En Windows también se puede usar `ejecutar.bat`, pero conviene revisar antes sus valores de `RUTA_BD_CONTACTOS`, `APP_PORT_CONTACTOS` y `SECRET_KEY`, ya que contiene una ruta local específica.

Abre `http://localhost:5000` o el puerto que hayas configurado.

En el primer arranque `run.py` crea las tablas SQLite y carga los tipos y valores iniciales. El fichero se guarda en `data/contactos.db`, salvo que se haya definido `RUTA_BD_CONTACTOS`.

## Primer uso

1. Accede a `/registro` y crea el primer usuario.
2. Inicia sesión desde `/login`.
3. Gestiona tus contactos desde `/personas/`.

Los usuarios nuevos no son administradores. El alta y la modificación de usuarios y etiquetas requieren permisos de administrador; el proyecto no incluye un comando CLI para promocionar automáticamente el primer usuario.

## Funcionalidades

- **Personas:** alta, edición, baja lógica, búsqueda por nombre o contacto y filtrado por etiqueta.
- **Datos asociados:** teléfonos, emails, direcciones, webs, lugares de contacto, eventos y relaciones entre personas.
- **Etiquetas:** categorías globales administradas desde `/etiquetas/`.
- **Importación:** carga de CSV exportado desde Google Contacts mediante la opción *Google CSV*.
- **Usuarios:** administración desde `/usuarios/` para usuarios con permisos de administrador.
- **Perfil:** edición del nombre, email y contraseña desde el menú del usuario.

La importación solo aplica las etiquetas que ya existen en la aplicación. Las operaciones de borrado utilizan baja lógica cuando corresponde, por lo que los registros pueden conservarse para auditoría.

## Estructura del proyecto

```text
.
├── run.py                    # Punto de entrada; inicializa BD y arranca Flask
├── ejecutar.bat              # Arranque auxiliar para Windows
├── requirements.txt          # Dependencias Python
├── app/
│   ├── app.py                # Instancia Flask, extensiones y blueprints
│   ├── config.py             # Variables de entorno y conexión SQLite
│   ├── comunes/              # Logger y utilidades compartidas
│   ├── personas/             # Contactos, modelos, formularios y rutas
│   ├── etiquetas/            # Gestión de etiquetas
│   ├── tipos_valores/        # Catálogos de eventos, relaciones y contactos
│   ├── usuarios/             # Login, registro y administración de usuarios
│   ├── static/               # CSS, JavaScript e imágenes
│   └── templates/             # Plantillas Jinja agrupadas por funcionalidad
├── data/                     # Logs y, en ejecución, contactos.db
├── docker/
│   ├── docker-compose.yaml   # Configuración para despliegue Docker/NAS
│   └── ejecutar.sh           # Instala dependencias y arranca la aplicación
└── versiones/                # Copias de versiones anteriores del proyecto
```

## Docker y NAS

`docker/docker-compose.yaml` está preparado para un entorno NAS concreto: usa `network_mode: host`, monta `/volume1/docker/python_bd/sqlite` y espera un fichero `.env` junto al compose. Antes de usarlo, revisa esos volúmenes y la ruta de la base de datos para tu instalación.

Desde el directorio `docker`:

```bash
docker compose up -d
docker compose logs -f python-17-contactos
```

El contenedor ejecuta `docker/ejecutar.sh`, que instala las dependencias y lanza `run.py`. Para detenerlo:

```bash
docker compose down
```

La imagen necesita acceso de escritura al directorio donde se guarde SQLite. Haz una copia de seguridad de `contactos.db` antes de actualizar o mover el despliegue.

## Producción y seguridad

- Usa una `SECRET_KEY` larga, aleatoria y distinta por instalación; no la guardes en el repositorio.
- Mantén `DEBUG=False` y sirve la aplicación detrás de un proxy inverso con HTTPS.
- Restringe el acceso al puerto y protege el fichero SQLite y los logs.
- Realiza copias de seguridad periódicas de la base de datos.

## Solución de problemas

- **No arranca:** comprueba que el entorno virtual está activo, que instalaste `requirements.txt` y que `SECRET_KEY` está definida.
- **El puerto está ocupado:** define otro, por ejemplo `APP_PORT_CONTACTOS=5012`, y abre el nuevo puerto en el navegador.
- **No aparece la base de datos:** verifica que el proceso tiene permisos de escritura sobre `data/` o sobre la ruta indicada por `RUTA_BD_CONTACTOS`.
- **Falla la importación:** usa un CSV exportado desde Google Contacts con **Exportar → Google CSV**, no un fichero vCard.
- **No puedo gestionar etiquetas o usuarios:** esas operaciones requieren una cuenta administradora.
