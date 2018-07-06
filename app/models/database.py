from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app import db


class CRUDMixin(object):

    @classmethod
    def get_items_with_keyvalue_dict(cls, kv_dict):
        items = db.session.query(cls).filter_by(**kv_dict).all()
        return items

    @classmethod
    def create(cls, commit=True, **kwargs):
        new_obj = cls(**kwargs)
        return new_obj.save(commit=commit)

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def update(self, commit=True, **kwargs):
        # prevent changing id
        kwargs.pop('id', None)
        for attr, value in kwargs.items():
            if not hasattr(self, attr):
                raise AttributeError(
                    '{} is not an attribute of {}'.format(attr, self))
            setattr(self, attr, value)
        if commit:
            self.save()
        else:
            return self

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
        if id is None:
            return None
        item = db.session.query(cls).get(id)
        return item

    @classmethod
    def get_with_ids(cls, ids):
        if ids is None:
            return None
        return db.session.query(cls).filter(cls.id.in_(ids)).all()

    # def __repr__(self):
    #     return '<{}>:{}'.format(self.__class__.__name__, self.id)


class TimestampMixin(object):
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
