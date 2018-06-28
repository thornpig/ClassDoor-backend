from datetime import datetime
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

    organization_assocations = db.relationship(
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

    __mapper__args = {
        'polymorphic_identity': 'person',
        'polymorphic_on': type
    }

    __table_args__ = (db.CheckConstraint(
        db.and_(db.text('length(first_name) > 0'),
                db.text('length(last_name) > 0'))),)

    @hybrid_property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __repr__(self):
        return '<{} {} {}>'.format(self.__class__.__name__, self.first_name,
                                   self.last_name)
