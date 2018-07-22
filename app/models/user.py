from sqlalchemy.ext.hybrid import hybrid_property
from .database import db, Model, SurrogatePK, TimestampMixin


class Person(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'person'
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(50))

    enrollments = db.relationship(
        'Enrollment',
        foreign_keys='[Enrollment.enrolled_person_id]',
        #  cascade="all, delete-orphan",
        back_populates='enrolled_person'
    )

    organization_person_associations = db.relationship(
        'OrganizationPersonAssociation',
        foreign_keys='[OrganizationPersonAssociation.associated_person_id]',
        #  cascade="all, delete-orphan",
        back_populates='associated_person'
    )

    notification_deliveries = db.relationship(
        'NotificationDelivery',
        foreign_keys='[NotificationDelivery.receiver_id]',
        back_populates='receiver',
        lazy='dynamic'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': type,
        # 'with_polymorphic': '*'
    }

    __table_args__ = (db.CheckConstraint(
        db.and_(db.text('length(first_name) > 0'),
                db.text('length(last_name) > 0'))),)

    @hybrid_property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __repr__(self):
        return '{} {} {}'.format(super().__repr__(),
                                 self.first_name, self.last_name)


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

    created_class_sessions = db.relationship(
        'ClassSession',
        foreign_keys='[ClassSession.creator_id]',
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


class Dependent(Person):
    __tablename__ = 'dependent'
    id = db.Column(db.ForeignKey('person.id'), primary_key=True)
    first_name = db.Column('dp_first_name', db.String(30), nullable=False)
    last_name = db.Column('dp_last_name', db.String(30), nullable=False)
    dependency_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    __table_args__ = (
        db.CheckConstraint(
            db.and_(db.text('length(dp_first_name) > 0'),
                    db.text('length(dp_last_name) > 0'))),
        db.UniqueConstraint(
            'dependency_id', 'dp_first_name', 'dp_last_name',
            name='dependent_name_dependency_id_unique')
    )

    __mapper_args__ = {
        'polymorphic_identity': 'dependent',
    }

