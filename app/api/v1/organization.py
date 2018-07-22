from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import (APIConst, Organization, OrganizationPersonAssociation,
                        User, Person)
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class OrganizationPersonSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = OrganizationPersonAssociation
    organization_id = fields.Integer(
        requried=True,
        validate=validate.Range(min=1),
    )
    associated_person_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    initiator_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    terminated = fields.Boolean()
    organization = fields.Nested(
        'OrganizationSchema',
        only=['id', '_type', 'name', 'creator_id'],
        dump_only=True,
    )
    associated_person = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        dump_only=True,
    )

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(User, data.get('initiator_id'))
        self.validate_item_existence_with_id(Organization,
                                             data.get('organization_id'))
        self.validate_item_existence_with_id(Person,
                                             data.get('associated_person_id'))


class OrganizationSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Organization
    name = fields.String(required=True,
                         validate=validate.Length(min=1, max=100))
    creator_id = fields.Integer(required=True, validate=validate.Range(min=1))
    organization_person_associations = fields.Nested(
        'OrganizationPersonSchema',
        only=['id', '_type', 'associated_person_id', 'terminated'],
        many=True,
        dump_only=True,
    )
    creator = fields.Nested(
        'UserSchema',
        only=['id', '_type', 'username', 'email', 'first_name', 'last_name'],
        dump_only=True,
    )

    @validates_schema
    def validate_creator_id(self, data):
        self.validate_item_existence_with_id(User, data.get('creator_id'))


orgper_schema = OrganizationPersonSchema()
orgpers_schema = OrganizationPersonSchema(many=True)
orgper_patch_schema = OrganizationPersonSchema(
    only=['terminated'])

organization_schema = OrganizationSchema()
organizations_schema = OrganizationSchema(many=True)
organization_patch_schema = OrganizationSchema(
    exclude=['creator_id'],
    partial=True
)

class OrganizationPersonResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            OrganizationPersonAssociation, orgper_schema, id)

    def patch(self, id):
        orgper = self.get_resource_with_ids(OrganizationPersonAssociation, id)
        json_data = request.get_json()
        try:
            data = orgper_patch_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            orgper.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = orgper_schema.dump(
            OrganizationPersonAssociation.get_with_id(orgper.id))
        response = jsonify({
            APIConst.MESSAGE:
            'updated organization person association {}'.format(id),
            APIConst.DATA: result})
        return response


class OrganizationPersonCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            OrganizationPersonAssociation, orgper_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = orgper_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)

        orgper = OrganizationPersonAssociation.create(**data)
        result = orgper_schema.dump(orgper)
        response = jsonify(
            {APIConst.MESSAGE: 'created new organization',
             APIConst.DATA: result})
        return response


class OrganizationResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Organization, organization_schema, id)

    def patch(self, id):
        organization = self.get_resource_with_ids(Organization, id)
        json_data = request.get_json()
        try:
            data = organization_patch_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            organization.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = organization_schema.dump(
            Organization.get_with_id(organization.id))
        response = jsonify({
            APIConst.MESSAGE: 'updated organization {}'.format(id),
            APIConst.DATA: result})
        return response


class OrganizationCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            Organization, organization_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = organization_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)

        organization = Organization.create(**data)
        result = organization_schema.dump(organization)
        response = jsonify(
            {APIConst.MESSAGE: 'created new organization',
             APIConst.DATA: result})
        return response



orgper_view = OrganizationPersonResource.as_view('orgper_api')
orgper_collection_view = OrganizationPersonCollectionResource.as_view(
    'orgper_collection_api')
bp.add_url_rule('/org-per-assns/<int:id>',
                view_func=orgper_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/org-per-assns/<int_list:ids>',
                view_func=orgper_collection_view,
                methods=['GET'])
bp.add_url_rule('/org-per-assns',
                view_func=orgper_collection_view,
                methods=['GET', 'POST'])

organization_view = OrganizationResource.as_view('organization_api')
organization_collection_view = OrganizationCollectionResource.as_view(
    'organization_collection_api')
bp.add_url_rule('/organizations/<int:id>',
                view_func=organization_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/organizations/<int_list:ids>',
                view_func=organization_collection_view,
                methods=['GET'])
bp.add_url_rule('/organizations',
                view_func=organization_collection_view,
                methods=['GET', 'POST'])
