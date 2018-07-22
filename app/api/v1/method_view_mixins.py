from flask import request, g, abort, jsonify
from flask.views import MethodView
from app.errors import RequestException
from app.models import APIConst, Model
from marshmallow import Schema


class BaseMethodViewMixin(object):

    def get_resource_with_ids(self, item_class, ids):
        if ids is None:
            raise RequestException('Bad request', 400)

        if not issubclass(item_class, Model):
            raise ValueError('item_class has to be a subclass of Model', 500)

        id_list = ids if isinstance(ids, list) else [ids]
        items = []
        for id in id_list:
            item = item_class.get_with_id(id)
            if item is None:
                raise RequestException(
                    '{} {} could not be found'.format(
                        item_class.__name__, id), 404)
            items.append(item)
        return items if isinstance(ids, list) else items[0]

    def get_resource_with_keyvalue_dict(self, item_class, kv_dict,
                                        unique=False):
        if kv_dict is None:
            raise RequestException()
        if not issubclass(item_class, Model):
            raise ValueError('item_class has to be a subclass of Model', 500)

        try:
            items = item_class.get_items_with_keyvalue_dict(kv_dict)
        except Exception:
            raise RequestException(
                'query cannot be completed with input data'.format(
                    item_class.__name__),
                400,
                {APIConst.INPUT: kv_dict})

        if not unique:
            return items
        else:
            count = len(items)
            if count == 0:
                raise RequestException(
                    '{} cannot be found with input query'.format(
                        item_class.__name__),
                    404,
                    {APIConst.INPUT: kv_dict})
            elif count > 1:
                raise RequestException(
                    '{} found with input query is not unique'.format(
                        item_class.__name__),
                    400,
                    {APIConst.INPUT: kv_dict})
            return items[0]

    def response_to_get_with_ids(self, item_class, schema_or_callable, ids):

        if ids is None:
            raise RequestException()

        if not issubclass(item_class, Model):
            raise ValueError('item_class has to be a subclass of Model', 500)

        if not isinstance(schema_or_callable, Schema) and not callable(
                schema_or_callable):
            print(schema_or_callable)
            raise ValueError(
                'schema_or_callable has to be an instance of'
                'marshmallow.Schema'
                'or a callable that return such an instance.', 500)

        id_list = ids if isinstance(ids, list) else [ids]
        items = self.get_resource_with_ids(item_class, id_list)

        schema_callable = schema_or_callable
        if not callable(schema_or_callable):
            schema_callable = (lambda obj: schema_or_callable)

        result = []
        for item in items:
            item_dict = schema_callable(item).dump(item)
            result.append(item_dict)

        if not isinstance(ids, list):
            return jsonify({APIConst.DATA: result[0]})
        return jsonify({APIConst.DATA: result})

    def response_to_get_with_keyvalue_dict(self, item_class,
                                           schema_or_callable,
                                           kv_dict,
                                           unique=False):
        if kv_dict is None:
            raise RequestException()

        if not issubclass(item_class, Model):
            raise ValueError('item_class has to be a subclass of Model', 500)

        if not isinstance(schema_or_callable, Schema) and not callable(
                schema_or_callable):
            raise ValueError(
                'schema_or_callable has to be an instance of'
                'marshmallow.Schema'
                'or a callable that return such an instance.', 500)

        items = self.get_resource_with_keyvalue_dict(item_class, kv_dict,
                                                     unique)
        items = [items] if unique else items
        schema_callable = schema_or_callable
        if not callable(schema_or_callable):
            schema_callable = (lambda obj: schema_or_callable)

        result = []
        for item in items:
            item_dict = schema_callable(item).dump(item)
            result.append(item_dict)

        if unique:
            return jsonify({APIConst.DATA: result[0]})
        return jsonify({APIConst.DATA: result})
