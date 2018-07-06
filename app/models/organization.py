# import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from .database import db, Model, SurrogatePK, TimestampMixin


class OrganizationPersonAssociation(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'organization_person_association'
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey('organization.id'),
    )
    associated_person_id = db.Column(
        db.Integer,
        db.ForeignKey('person.id'),
    )
    terminated = db.Column(db.Boolean, nullable=False, default=False)
    initiator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    organization = db.relationship(
        'Organization',
        back_populates='organization_person_associations',
        lazy='subquery'
    )

    associated_person = db.relationship(
        'Person',
        back_populates='organization_person_associations',
        lazy='subquery'
    )


class Organization(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'organization'

    name = db.Column(db.String(100), nullable=None)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=None)

    organization_person_associations = db.relationship(
        'OrganizationPersonAssociation',
        foreign_keys='[OrganizationPersonAssociation.organization_id]',
        #  cascade="all, delete-orphan",
        back_populates='organization'
    )

    creator = db.relationship(
        'User',
        backref='created_organizations',
        lazy='subquery'
    )

    def __repr__(self):
        return '<Organization> {} created by {}'.format(self.name,
                                                        self.creator.username)

