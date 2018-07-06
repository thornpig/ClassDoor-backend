from marshmallow import (Schema, fields, validate, ValidationError, pprint)
from app.models import Model


class BaseSchemaMixin(object):
    #  To be set by sub class
    __model__ = None
    id = fields.Integer(dump_only=True)
    _type = fields.Method('get_type', dump_only=True)

    def get_type(self, obj):
        return self.__model__.__name__

    def validate_item_existence_with_id(self, item_class, id):
        if id is None:
            return
        if not issubclass(item_class, Model):
            raise ValueError('item_class has to be a subclass of Model', 500)

        item = item_class.get_with_id(id)
        if item is None:
            raise ValidationError('{} {} cannot be found'.format(
                item_class.__name__, id))


class TimestampSchemaMixin(object):
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
