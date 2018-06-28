from .database import db
from .person import Person


class User(Person):
    __tablename__ = 'user'
    id = db.Column(db.ForeignKey('person.id'), primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    dependents = db.relationship(
        'Dependent',
        foreign_keys='[Dependent.dependency_id]',
        backref='dependency',
        lazy='dynamic'
    )

    created_classes = db.relationship(
        'Class',
        foreign_keys='[Class.creator_id]',
        backref='creator',
        lazy='dynamic'
    )

    initiated_enrollments = db.relationship(
        'Enrollment',
        foreign_keys='[Enrollment.initiator_id]',
        backref='initiator',
        lazy='dynamic'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @classmethod
    def get_with_username(cls, username):
        return cls.query.filter_by(username=username).first()
