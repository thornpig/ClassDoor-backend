from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event
from .database import db, Model, SurrogatePK, TimestampMixin
from .lesson import Lesson, RepeatedLesson


class_address_association = (
    db.Table('class_address_association',
             db.Column('class_id', db.Integer, db.ForeignKey('class.id'),
                       primary_key=True),
             db.Column('address_id', db.Integer, db.ForeignKey('address.id'),
                       primary_key=True)
             )
)

class_instructor_association = (
    db.Table('class_instructor_association',
             db.Column('class_id', db.Integer,
                       db.ForeignKey('class.id'),
                       primary_key=True),
             db.Column('instructor_id', db.Integer, db.ForeignKey('person.id'),
                       primary_key=True)
             )
)


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


class Class(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'class'
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    #  duration is in minutes
    duration = db.Column(db.Integer, nullable=False, default=30)
    num_of_lessons_per_session = db.Column(
        db.Integer)
    capacity = db.Column(db.Integer)
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))

    locations = db.relationship(
        'Address',
        secondary=class_address_association,
        lazy='subquery',
        backref=db.backref('classes', lazy='dynamic')
    )

    sessions = db.relationship(
        'ClassSession',
        lazy='subquery',
        backref='parent_class'
    )

    instructors = db.relationship(
        'Person',
        secondary=class_instructor_association,
        lazy='subquery',
        backref=db.backref('instructed_classes', lazy='dynamic')
    )

    organization = db.relationship(
        'Organization',
        lazy='subquery',
        backref=db.backref('classes', lazy='dynamic')
    )

    __table_args__ = (
        db.CheckConstraint(db.text('length(title) > 0')),
        db.UniqueConstraint('title', 'creator_id',
                            name='title_creator_unique'),
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

    instructors = db.relationship(
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
        backref=db.backref('class_session', lazy='subquery'),
        enable_typechecks=False
    )

    @hybrid_property
    def num_of_enrollments(self):
        pass

    def create_lessons(self):
        lessons = []
        for tl in self.template_lessons:
            start_at = tl.time_slot.start_at
            index_of_rep = 0
            while start_at < self.schedule.repeat_end_at:
                lesson = RepeatedLesson(index_of_rep=index_of_rep,
                                        template_lesson=tl,
                                        class_session=self)
                lessons.append(lesson)
                start_at = self.schedule.repeat_option.get_repeat_datetime(
                    start_at, 1)
                index_of_rep += 1
        return lessons

    def create_lessons_for_template_lesson(self, tl):
        lessons = []
        start_at = tl.time_slot.start_at
        index_of_rep = 0
        while start_at < self.schedule.repeat_end_at:
            lesson = RepeatedLesson(index_of_rep=index_of_rep,
                                    template_lesson=tl,
                                    class_session=self)
            lessons.append(lesson)
            start_at = self.schedule.repeat_option.get_repeat_datetime(
                start_at, 1)
            index_of_rep += 1
        return lessons

    def __repr__(self):
        return '{} of {}'.format(super().__repr__(),
                                 self.parent_class)


#  @event.listens_for(ClassSession.template_lessons, 'append')
#  def receive_template_lessons_append(target, value, initiator):
#      if value not in target.template_lessons.all():
#          new_repeated_lessons = target.create_lessons_for_template_lesson(value)
#          for nrl in new_repeated_lessons:
#              target.lessons.append(nrl)


#  @event.listens_for(Team.users, 'remove')
#  def receive_team_users_append(target, value, initiator):
#          print(value.name, 'removed from team', target.name)
