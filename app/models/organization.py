from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from .database import db, Model, SurrogatePK, TimestampMixin


class OrganizationPersonAssociation(TimestampMixin, Model):
    __tablename__ = 'organization_person_association'
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey('organization.id'),
        primary_key=True
    )
    associated_person_id = db.Column(
        db.Integer,
        db.ForeignKey('person.id'),
        primary_key=True
    )
    terminated = db.Column(db.Boolean, nullable=False, default=False)
    initiator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    organization = db.relationship(
        'Organization',
        back_populates='organization_associations',
        lazy='subquery'
    )

    associated_person = db.relationship(
        'Person',
        back_populates='organization_assocations',
        lazy='subquery'
    )


class Organization(SurrogatePK, TimestampMixin, Model):
    __tablename__ = 'organization'

    name = db.Column(db.String(100), nullable=None)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=None)

    organization_associations = db.relationship(
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

