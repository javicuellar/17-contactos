from flask import Blueprint



contactos_bp = Blueprint('contactos', __name__)

from . import routes