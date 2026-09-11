from flask import Blueprint



usuarios_bp = Blueprint('usuarios', __name__)

from . import routes