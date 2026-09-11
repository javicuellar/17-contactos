from flask import Blueprint



etiquetas_bp = Blueprint('etiquetas', __name__)

from . import routes