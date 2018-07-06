from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.routing import BaseConverter, Rule, Map


db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    configure_extensions(app)
    register_url_converters(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


def configure_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    from .routes import bp as bp_routes
    from .api.v1 import bp as bp_api
    from .errors import bp as bp_err
    app.register_blueprint(bp_routes)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_err)


def register_error_handlers(app):
    from .errors import request_exception as e
    e.register_request_exception_handlers(app)


def register_url_converters(app):
    # url converters need to be registered
    # before the blueprint registers the url rules!
    from .api.url_converters import IntListConverter
    app.url_map.converters['int_list'] = IntListConverter


from .models import (address, user, enrollment,
                     class_session, schedule)
