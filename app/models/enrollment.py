from .database import db, Model, SurrogatePK, TimestampMixin
from .class_session import ClassSession
from .user import Person, User


class Enrollment(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'enrollment'
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'))
    enrolled_person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    terminated = db.Column(db.Boolean, nullable=False, default=False)
    initiator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    class_session = db.relationship(
        'ClassSession',
        back_populates='enrollments',
        lazy='subquery'
    )
    enrolled_person = db.relationship(
        'Person',
        back_populates='enrollments',
        lazy='subquery'
    )

    def __repr__(self):
        return '{} for {} in {}'.format(
            super().__repr__(),
            self.enrolled_person,
            self.class_session
        )

    @classmethod
    def get_enrollments(cls, class_session_id=None, enrolled_person_id=None,
                        initiator_id=None):
        if (class_session_id is not None
                and enrolled_person_id is None
                and initiator_id is None):
            class_session = ClassSession.get_with_id(class_session_id)
            return class_session.enrollments[:]

        elif (class_session_id is None
                and enrolled_person_id is not None
                and initiator_id is None):
            enrolled_person = Person.get_with_id(enrolled_person_id)
            return enrolled_person.enrollments[:]
        elif (class_session_id is None
                and enrolled_person_id is None
                and initiator_id is not None):
            initiator = User.get_with_id(initiator_id)
            return initiator.initiated_enrollments[:]
        elif (class_session_id is not None
              and enrolled_person_id is not None
              and initiator_id is None):
            return db.session.query(Enrollment).filter(
                Enrollment.class_session_id == class_session_id,
                Enrollment.enrolled_person_id == enrolled_person_id).all()
