from app import create_app, db
from app.models import Person, User, Dependent, Class, Address

app = create_app()


@app.teardown_request
def sqlalchemy_session_cleanup(exception=None):
    if exception:
        db.session.rollback()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Person': Person, 'User': User,
            'Dependent': Dependent, 'Class': Class, 'Address': Address}
