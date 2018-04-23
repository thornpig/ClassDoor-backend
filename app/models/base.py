from app import db


class BaseMixin(object):
    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def get_with_id(cls, id):
        item = cls.query.get(id)
        return item
