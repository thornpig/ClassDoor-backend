from datetime import datetime
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.base import NO_VALUE
from .database import db, Model, SurrogatePK, TimestampMixin


template_lesson_instructor_association = (
    db.Table('template_lesson_instructor_association',
             db.Column('template_lesson_id', db.Integer,
                       db.ForeignKey('template_lesson.id'),
                       primary_key=True),
             db.Column('instructor_id', db.Integer, db.ForeignKey('person.id'),
                       primary_key=True)
             )
)

lesson_instructor_association = (
    db.Table('lesson_instructor_association',
             db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'),
                       primary_key=True),
             db.Column('instructor_id', db.Integer, db.ForeignKey('person.id'),
                       primary_key=True)
             )
)

lesson_guest_student_association = (
    db.Table('lesson_guest_student_association',
             db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'),
                       primary_key=True),
             db.Column('guest_student_id', db.Integer,
                       db.ForeignKey('person.id'),
                       primary_key=True)
             )
)

#  template_lesson_address_association = (
#      db.Table('template_lesson_address_association',
#               db.Column('template_lesson_id', db.Integer,
#                         db.ForeignKey('template_lesson.id'),
#                         primary_key=True),
#               db.Column('address_id', db.Integer, db.ForeignKey('address.id'),
#                         primary_key=True)
#               )
#  )


class TemplateLesson(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'template_lesson'
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'))
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('address.id')
    )
    class_session_id = db.Column(
        db.Integer,
        db.ForeignKey('class_session.id')
    )

    time_slot = db.relationship(
        'TimeSlot',
        lazy='subquery'
    )

    instructors = db.relationship(
        'Person',
        secondary=template_lesson_instructor_association,
        lazy='subquery'
    )

    location = db.relationship(
        'Address',
        lazy='subquery'
    )

    #  locations = db.relationship(
    #      'Address',
    #      secondary=template_lesson_address_association,
    #      lazy='subquery'
    #  )
@event.listens_for(TemplateLesson.class_session_id, 'set')
def link_template_lesson_to_class_session_id(
        target, value, oldvalue, initiator):
    from . import ClassSession, TimeSlot
    if (value is not None and oldvalue == NO_VALUE and
            target.time_slot_id is not None):
        class_session = ClassSession.get_with_id(value)
        target.time_slot = TimeSlot.get_with_id(target.time_slot_id)
        db.session.add_all(
            class_session.create_lessons_for_template_lesson(target))
    elif (value is None and oldvalue is not NO_VALUE):
        class_session = ClassSession.get_with_id(oldvalue)
        lessons = db.session.query(RepeatedLesson).filter_by(
            template_lesson_id=target.id).all()
        for lesson in lessons:
            lesson.class_session_id = None
        db.session.add_all(lessons)


@event.listens_for(TemplateLesson.time_slot_id, 'set')
def link_template_lesson_to_class_session_id(
        target, value, oldvalue, initiator):
    from . import ClassSession, TimeSlot
    if (value is not None and oldvalue == NO_VALUE and
            target.class_session_id is not None):
        class_session = ClassSession.get_with_id(target.class_session_id)
        target.time_slot = TimeSlot.get_with_id(value)
        db.session.add_all(
            class_session.create_lessons_for_template_lesson(target))


class Lesson(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'lesson'

    type = db.Column(db.String(50))
    start_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer)

    class_session_id = db.Column(
        db.Integer,
        db.ForeignKey('class_session.id'),
        index=True,
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey('address.id')
    )

    instructors = db.relationship(
        'Person',
        secondary=lesson_instructor_association,
        lazy='subquery',
        backref=db.backref('instructed_lessons', lazy='dynamic')
    )

    guest_students = db.relationship(
        'Person',
        secondary=lesson_guest_student_association,
        lazy='subquery',
        backref=db.backref('visiting_lessons', lazy='subquery')
    )

    location = db.relationship(
        'Address',
        lazy='subquery'
    )

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type,
    }


class RepeatedLesson(Lesson):
    __tablename__ = 'repeated_lesson'
    id = db.Column(db.ForeignKey('lesson.id'), primary_key=True)
    template_lesson_id = db.Column(
        db.Integer,
        db.ForeignKey('template_lesson.id'),
    )
    index_of_rep = db.Column(db.Integer, default=0, nullable=False)

    template_lesson = db.relationship(
        'TemplateLesson',
        lazy='subquery'
    )

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

