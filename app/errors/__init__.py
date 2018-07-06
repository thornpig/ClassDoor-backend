from flask import Blueprint

bp = Blueprint('errors', __name__)

from .request_exception import RequestException
