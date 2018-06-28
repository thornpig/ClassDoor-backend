from datetime import datetime
from app import db


class CRUDMixin(object):

    @classmethod
    def get_with_id(cls, id):
        item = cls.query.get(id)
        return item

    @classmethod
    def create(cls, **kwargs):
        new_obj = cls(**kwargs)
        return new_obj.save()

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def update(self, commit=True, **kwargs):
        # prevent changing id
        kwargs.pop('id', None)
        for attr, value in kwargs.items:
            if value is not None:
                setattr(self, attr, value)
            return self.save() if commit else self

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()


class Model(CRUDMixin, db.Model):
    __abstract__ = True


class SurrogatePK(object):
    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def get_with_id(cls, id):
        item = cls.query.get(id)
        return item

    def __repr__(self):
        return '<{}> id: {}'.format(self.__class__.__name__, self.id)


class TimestampMixin(object):
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
