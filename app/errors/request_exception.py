from flask import jsonify
from . import bp


class RequestException(Exception):
    __abstract__ = True

    def __init__(self, message='Bad request', status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = self.status_code
        return rv


# @bp.errorhandler(RequestException)  not working....
def handle_request_exception(error):
    response = jsonify({"errors": [error.to_dict()]})
    response.status_code = error.status_code
    return response


def register_request_exception_handlers(app):
    app.register_error_handler(RequestException,
                               handle_request_exception)

