from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import generate_csrf

from app import config
from app.comunes.logger import get_logger

log = get_logger('app')




app = Flask(__name__)
app.config.from_object(config)

Bootstrap(app)

# Inyectar csrf_token como función global en todos los templates (incluidos via {% include %})
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Forzar español independientemente del idioma del navegador
@app.before_request
def set_locale():
    pass

# Sobrescribir la detección de locale de Flask-Bootstrap
app.config['BABEL_DEFAULT_LOCALE'] = 'es'

# Parche: evitar que Jinja/Bootstrap use el Accept-Language del navegador
from flask import g
@app.before_request
def force_spanish():
    g.locale = 'es'

db = SQLAlchemy(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        app.root_path + '/static',
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"



# Registro de los Blueprints
from .usuarios import usuarios_bp
app.register_blueprint(usuarios_bp)

from .personas import personas_bp
app.register_blueprint(personas_bp)

from .etiquetas import etiquetas_bp
app.register_blueprint(etiquetas_bp)

from .tipos_valores import tipos_valores_bp
app.register_blueprint(tipos_valores_bp)
