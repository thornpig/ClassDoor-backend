from app import create_app, db
from app.models.user import User
from app.models.post import Post

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}



