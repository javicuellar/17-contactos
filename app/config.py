import os




# Forzar idioma español (evita que Flask-Bootstrap use el idioma del navegador)
BABEL_DEFAULT_LOCALE = 'es'
BABEL_DEFAULT_TIMEZONE = 'Europe/Madrid'

# Configuración de la base de datos y Flask
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG")

# PWD = os.path.abspath(os.curdir) + '/data'
# SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/contactos.db'.format(PWD)
RUTA_BD_CONTACTOS = os.environ.get("RUTA_BD_CONTACTOS") or     os.path.join(os.path.abspath(os.curdir), 'instancias', 'contactos.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{RUTA_BD_CONTACTOS}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
