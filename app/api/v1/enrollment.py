from flask import request, g, abort, jsonify
from flask.views import MethodView
from marshmallow import (Schema, fields, validate, ValidationError,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import (APIConst, Enrollment, Person, User, ClassSession)
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class EnrollmentSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Enrollment
    class_session_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    enrolled_person_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    initiator_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    terminated = fields.Boolean()
    class_session = fields.Nested(
        'ClassSessionSchema',
        only=['id', '_type', 'class_id', 'creator_id', 'schedule_id'],
        dump_only=True,
    )
    enrolled_person = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        dump_only=True,
    )
    initiator = fields.Nested(
        'UserSchema',
        only=['id', '_type', 'username', 'email', 'first_name', 'last_name'],
        dump_only=True,
    )

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(ClassSession,
                                             data.get('class_session_id'))
        self.validate_item_existence_with_id(Person,
                                             data.get('enrolled_person_id'))
        self.validate_item_existence_with_id(User,
                                             data.get('initiator_id'))


enrollment_schema = EnrollmentSchema()
enrollments_schema = EnrollmentSchema(many=True)
enrollment_patch_schema = EnrollmentSchema(
    only=['terminated'],
)


class EnrollmentResource(BaseMethodViewMixin, MethodView):

    def get(self, id):
        return self.response_to_get_with_ids(
            Enrollment, enrollment_schema, id)

    def patch(self, id):
        enrollment = self.get_resource_with_ids(Enrollment, id)
        json_data = request.get_json()
        try:
            data = enrollment_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            enrollment.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = enrollment_schema.dump(Enrollment.get_with_id(
            enrollment.id))
        response = jsonify({APIConst.MESSAGE: 'updated enrollment {}'.format(
            id), APIConst.DATA: result})
        
        return response


class EnrollmentCollectionResource(BaseMethodViewMixin, MethodView):
    def get(self, ids=None):
        return self.response_to_get_with_ids(Enrollment,
                                             enrollment_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = enrollment_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        enrollment = Enrollment.create(**data)
        result = enrollment_schema.dump(enrollment)
        response = jsonify(
            {APIConst.MESSAGE: 'created new enrollment',
             APIConst.DATA: result})
        
        return response


enrollment_view = EnrollmentResource.as_view('enrollment_api')
enrollment_collection_view = EnrollmentCollectionResource.as_view(
    'enrollment_colection_api')
bp.add_url_rule('/enrollments/<int:id>',
                view_func=enrollment_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/enrollments/<int_list:ids>',
                view_func=enrollment_collection_view,
                methods=['GET'])
bp.add_url_rule('/enrollments',
                view_func=enrollment_collection_view,
                methods=['GET', 'POST'])

