from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import (APIConst, Class, ClassSession, Address, User,
                        Organization, Schedule)
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class ClassSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Class
    title = fields.String(required=True, validate=validate.Length(
        min=1, max=80))
    duration = fields.Integer(required=True,
                              validate=validate.Range(min=1))
    creator_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    organization_id = fields.Integer(validate=validate.Range(min=1))
    description = fields.String(validate=validate.Length(max=200))
    num_of_lessons_per_session = fields.Integer(
        validate=validate.Range(min=1))
    capacity = fields.Integer(validate=validate.Range(min=1))
    min_age = fields.Integer(validate=validate.Range(min=0))
    max_age = fields.Integer(validate=validate.Range(min=0))

    locations = fields.Nested('AddressSchema',
                              many=True, partial=True)
    sessions = fields.Nested(
        'ClassSessionSchema',
        only=['id', '_type', 'schedule_id', 'class_id', 'creator_id'],
        many=True,
        dump_only=True,
    )
    organization = fields.Nested(
        'OrganizationSchema',
        only=['id', '_type', 'name', 'creator_id'],
        dump_only=True,
    )
    creator = fields.Nested(
        'UserSchema',
        only=['id', '_type', 'username', 'email', 'first_name', 'last_name'],
        dump_only=True,
    )

    def load(self, data, many=None, partial=None):

        de_data = super().load(data, many=many, partial=partial)
        de_data = [de_data] if not many else de_data

        for de_data_item in de_data:
            location_dicts = de_data_item.get('locations')
            if location_dicts is None:
                continue
            locations = []
            for loc_dict in location_dicts:
                id = loc_dict.get('id')
                print(id)
                loc = None
                if id:
                    loc = Address.get_with_id(id)
                else:
                    loc = Address.create(commit=False, **loc_dict)
                locations.append(loc)
            de_data_item['locations'] = locations

        return de_data if many else de_data[0]

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(Organization,
                                             data.get('organization_id'))
        self.validate_item_existence_with_id(User,
                                             data.get('creator_id'))


class ClassSessionSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = ClassSession
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
    creator_id = fields.Integer(required=True, validate=validate.Range(min=1))
    schedule_id = fields.Integer(required=True, validate=validate.Range(min=1))

    capacity = fields.Integer(validate=validate.Range(min=1))
    template_lessons = fields.Nested(
        'TemplateLessonSchema',
        only=['id', '_type', 'time_slot', 'class_session_id'],
        many=True,
        dump_only=True,
    )
    creator = fields.Nested(
        'UserSchema',
        only=['id', '_type', 'username', 'email', 'first_name', 'last_name'],
        dump_only=True,
    )
    schedule = fields.Nested(
        'ScheduleSchema',
        dump_only=True,
    )
    enrollments = fields.Nested(
        'EnrollmentSchema',
        only=['id', '_type', 'enrolled_person_id', 'initiator_id',
              'terminated', 'class_session_id'],
        many=True,
        dump_only=True,
    )
    instructors = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        many=True,
        dump_only=True,
    )

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(Class,
                                             data.get('class_id'))
        self.validate_item_existence_with_id(User,
                                             data.get('creator_id'))
        self.validate_item_existence_with_id(Schedule,
                                             data.get('schedule_id'))


class_schema = ClassSchema()
classes_schema = ClassSchema(many=True)
class_patch_schema = ClassSchema(exclude=['id', 'creator_id'])

class_session_schema = ClassSessionSchema()
class_sessions_schema = ClassSessionSchema(many=True)
class_session_patch_schema = ClassSessionSchema(
    exclude=['class_id', 'creator_id'])


class ClassResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Class, class_schema, id)

    def patch(self, id):
        _class = self.get_resource_with_ids(Class, id)
        json_data = request.get_json()
        try:
            data = class_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            _class.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = class_schema.dump(Class.get_with_id(_class.id))
        response = jsonify({APIConst.MESSAGE: 'updated class {}'.format(id),
                            APIConst.DATA: result})
        
        return response


class ClassCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(Class, class_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = class_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        _class = Class.create(**data)
        result = class_schema.dump(_class)
        response = jsonify(
            {APIConst.MESSAGE: 'created new class',
             APIConst.DATA: result})
        
        return response


class ClassSessionResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            ClassSession, class_session_schema, id)

    def patch(self, id):
        class_session = self.get_resource_with_ids(ClassSession, id)
        json_data = request.get_json()
        try:
            data = class_session_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            class_session.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = class_session_schema.dump(ClassSession.get_with_id(
            class_session.id))
        response = jsonify({APIConst.MESSAGE: 'updated class session {}'.format(
            id), APIConst.DATA: result})
        
        return response


class ClassSessionCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            ClassSession, class_session_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = class_session_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        class_session = ClassSession.create(**data)
        result = class_session_schema.dump(class_session)
        response = jsonify(
            {APIConst.MESSAGE: 'created new class session',
             APIConst.DATA: result})
        
        return response


class_view = ClassResource.as_view('class_api')
class_collection_view = ClassCollectionResource.as_view(
    'class_collection_api')
bp.add_url_rule('/classes/<int:id>',
                view_func=class_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/classes/<int_list:ids>',
                view_func=class_collection_view,
                methods=['GET'])
bp.add_url_rule('/classes',
                view_func=class_collection_view,
                methods=['GET', 'POST'])

class_session_view = ClassSessionResource.as_view('class_session_api')
class_session_collection_view = ClassSessionCollectionResource.as_view(
    'class_session_collection_api')
bp.add_url_rule('/class-sessions/<int:id>',
                view_func=class_session_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/class-sessions/<int_list:ids>',
                view_func=class_session_collection_view,
                methods=['GET'])
bp.add_url_rule('/class-sessions',
                view_func=class_session_collection_view,
                methods=['GET', 'POST'])
