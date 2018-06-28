from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from .database import db, Model, SurrogatePK, TimestampMixin
from .lesson import Lesson

class_session_instructor_association = (
    db.Table('class_session_instructor_association',
             db.Column('class_session_id', db.Integer,
                       db.ForeignKey('class_session.id'),
                       primary_key=True),
             db.Column('instructor_id', db.Integer, db.ForeignKey('person.id'),
                       primary_key=True)
             )
)

class_session_address_association = (
    db.Table('class_session_address_association',
             db.Column('class_session_id', db.Integer,
                       db.ForeignKey('class_session.id'),
                       primary_key=True),
             db.Column('address_id', db.Integer, db.ForeignKey('address.id'),
                       primary_key=True)
             )
)


class ClassSession(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'class_session'
    capacity = db.Column(db.Integer)
    class_id = db.Column(
        db.Integer,
        db.ForeignKey('class.id'),
        nullable=False
    )
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey('schedule.id'),
        nullable=False
    )

    enrollments = db.relationship(
        'Enrollment',
        #  cascade="all, delete-orphan",
        back_populates='class_session', lazy='dynamic')

    schedule = db.relationship(
        'Schedule',
        cascade="all, delete-orphan",
        single_parent=True,
        lazy='subquery',
    )

    template_lessons = db.relationship(
        'TemplateLesson',
        cascade="all, delete-orphan",
        lazy='dynamic',
        backref='class_session'
    )

    instrctors = db.relationship(
        'Person',
        secondary=class_session_instructor_association,
        lazy='subquery',
        backref=db.backref('instructed_class_sessions', lazy='dynamic')
    )

    locations = db.relationship(
        'Address',
        secondary=class_session_address_association,
        lazy='subquery',
        backref=db.backref('class_sessions', lazy='dynamic')
    )

    lessons = db.relationship(
        'Lesson',
        lazy='dynamic',
        backref=db.backref('class_session', lazy='subquery')
    )


    @hybrid_property
    def num_of_enrollments(self):
        pass

    def create_lessons(self):
        template_lesson_dict = {tl.repeat_time_slot.get_start_at(): tl for
                                tl in self.template_lessons}
        lessons = []
        for repeat_slot in self.schedule.repeat_time_slots:
            tl = template_lesson_dict[repeat_slot.base_time_slot.start_at]
            lesson = Lesson(repeat_time_slot=repeat_slot, template_lesson=tl)
            lessons.append(lesson)
        return lessons


    def __repr__(self):
        return '<ClassSession> of {}'.format(self.parent_class)


