from flask_sqlalchemy import Model, SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr, has_inherited_table


class BaseModel(Model):
    @declared_attr
    def id(cls):
        for base in cls.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                type = sa.ForeignKey(base.id)
                break
        else:
            type = sa.Integer

        return sa.Column(type, primary_key=True)

    @classmethod
    def get_with_id(cls, id):
        item = cls.query.get(id)
        return item

    @classmethod
    def create(cls, **kwargs):
        new_obj = cls(**kwargs)
        return new_obj.save()

    def save(self, commit=True):
        from app import db
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
        from app import db
        db.session.delete(self)
        if commit:
            db.session.commit()


