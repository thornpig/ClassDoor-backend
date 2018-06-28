from .database import db, Model, SurrogatePK, TimestampMixin

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


class Class(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'class'
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
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

    def __repr__(self):
        return '<Class {}>'.format(self.title)
