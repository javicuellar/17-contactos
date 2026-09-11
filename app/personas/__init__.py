from flask import Blueprint




personas_bp = Blueprint('personas', __name__)

from . import routes