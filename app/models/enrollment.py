from .database import db, Model, TimestampMixin


class Enrollment(TimestampMixin, Model):
    __tablename__ = 'enrollment'
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'),
                                 primary_key=True)
    enrolled_person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                                   primary_key=True)
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
        return '<Enrollment> for {} in {}'.format(
            self.enrolled_person,
            self.class_session
        )
