from flask import Blueprint



tipos_valores_bp = Blueprint('tipos_valores', __name__)

from . import routes