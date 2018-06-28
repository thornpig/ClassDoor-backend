from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
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

template_lesson_address_association = (
    db.Table('template_lesson_address_association',
             db.Column('template_lesson_id', db.Integer,
                       db.ForeignKey('template_lesson.id'),
                       primary_key=True),
             db.Column('address_id', db.Integer, db.ForeignKey('address.id'),
                       primary_key=True)
             )
)


class TemplateLesson(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'template_lesson'
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('address.id')
    )
    repeat_time_slot_id = db.Column(
        db.Integer,
        db.ForeignKey('repeat_time_slot.id'),
        nullable=False
    )
    class_session_id = db.Column(
        db.Integer,
        db.ForeignKey('class_session.id'),
        nullable=False
    )

    instructors = db.relationship(
        'Person',
        secondary=template_lesson_instructor_association,
        lazy='subquery'
    )

    locations = db.relationship(
        'Address',
        secondary=template_lesson_address_association,
        lazy='subquery'
    )

    repeat_time_slot = db.relationship(
        'RepeatTimeSlot',
        lazy='subquery',
        backref=db.backref('template_lesson', lazy='dynamic')
    )


class Lesson(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'lesson'
    start_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    repeat_time_slot_id = db.Column(
        db.Integer,
        db.ForeignKey('repeat_time_slot.id'),
        nullable=False
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('address.id')
    )
    template_lesson_id = db.Column(
        db.Integer,
        db.ForeignKey('template_lesson.id'),
    )

    class_session_id = db.Column(
        db.Integer,
        db.ForeignKey('class_session.id'),
        nullable=False
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

    template_lesson = db.relationship(
        'TemplateLesson',
        lazy='subquery'
    )

    repeat_time_slot = db.relationship(
        'RepeatTimeSlot',
        lazy='subquery',
        backref=db.backref('lesson', lazy='dynamic')
    )
