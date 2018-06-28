from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from .database import db, Model, SurrogatePK, TimestampMixin


class NotificationDelivery(TimestampMixin, Model):
    __tablename__ = 'notification_person_delivery'
    notification_id = db.Column(
        db.Integer,
        db.ForeignKey('notification.id'),
        primary_key=True
    )
    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey('person.id'),
        primary_key=True
    )
    delivered_at = db.Column(db.DateTime)

    notification = db.relationship(
        'Notification',
        back_populates='deliveries',
        lazy='subquery'
    )

    receiver = db.relationship(
        'Person',
        back_populates='notification_deliveries',
        lazy='subquery'
    )


class Notification(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'notification'
    content = db.Column(db.String(200), nullable=False)
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('person.id'),
        nullable=False
    )

    deliveries = db.relationship(
        'NotificationDelivery',
        foreign_keys='[NotificationDelivery.notification_id]',
        back_populates='notification'
    )

    sender = db.relationship(
        'Person',
        lazy='subquery',
        backref=db.backref('posted_notifications', lazy='dynamic'),
    )

    def __repr__(self):
        return '<Notification> sent by {} : {}'.format(
            self.sender.full_name, self.content)
