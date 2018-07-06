from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError, pprint,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import APIConst, Address, User
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class AddressSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Address
    primary_street = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    secondary_street = fields.String(validate=validate.Length(min=1, max=100))
    city = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )
    state = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )
    zipcode = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )
    country = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )
    creator_id = fields.Integer(required=True,
                                validate=validate.Range(min=1))

    @validates_schema
    def validate_creator_id(self, data):
        self.validate_item_existence_with_id(User, data.get('creator_id'))


address_schema = AddressSchema()
addresses_schema = AddressSchema(many=True)
address_patch_schema = AddressSchema(exclude=['id', 'creator_id'])


class AddressResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Address, address_schema, id)

    def patch(self, id=None):
        address = self.get_resource_with_ids(Address, id)
        json_data = request.get_json()
        try:
            data = address_patch_schema.load(
                json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            address.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = address_schema.dump(Address.get_with_id(address.id))
        return jsonify({APIConst.MESSAGE: 'updated address {}'.format(id),
                        APIConst.DATA: result})


class AddressCollectionResource(BaseMethodViewMixin, MethodView):
    def get(self, ids=None):
        return self.response_to_get_with_ids(
            Address, address_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = address_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        address = Address.create(**data)
        result = address_schema.dump(address)
        return jsonify(
            {APIConst.MESSAGE: 'created new address', APIConst.DATA: result})


address_view = AddressResource.as_view('address_api')
address_collection_view = AddressCollectionResource.as_view(
    'address_collection_api')
bp.add_url_rule('/addresses/<int:id>',
                view_func=address_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/addresses/<int_list:ids>',
                view_func=address_collection_view,
                methods=['GET'])
bp.add_url_rule('/addresses',
                view_func=address_collection_view,
                methods=['GET', 'POST'])
