from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError, pprint,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import (APIConst, Lesson, RepeatedLesson, Address, TimeSlot,
                        ClassSession, TemplateLesson)
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class TemplateLessonSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = TemplateLesson
    time_slot_id = fields.Integer(required=True)
    class_session_id = fields.Integer(requird=True)
    location_id = fields.Integer()
    time_slot = fields.Nested(
        'TimeSlotSchema',
        dump_only=True,
    )
    instructors = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        many=True,
        dump_only=True,
    )
    location = fields.Nested('AddressSchema')
    class_session = fields.Nested(
        'ClassSessionSchema',
        only=['id', '_type', 'class_id', 'template_lessons'],
        dump_only=True)

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(ClassSession,
                                             data.get('class_session_id'))
        self.validate_item_existence_with_id(Address,
                                             data.get('location_id'))
        self.validate_item_existence_with_id(TimeSlot,
                                             data.get('time_slot_id'))


class LessonSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Lesson
    class_session_id = fields.Integer(required=True)
    start_at = fields.DateTime(required=True)
    duration = fields.Integer(required=True, validate=validate.Range(min=0))
    location_id = fields.Integer(validate=validate.Range(min=1))
    instructors = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        many=True,
        dump_only=True,
    )
    guest_students = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        many=True,
        dump_only=True,
    )
    location = fields.Nested('AddressSchema')

    @staticmethod
    def make_dynamic_schema(**kwargs):
        def dynamic_schema(lesson):
            type_of_lesson = type(lesson)
            if type_of_lesson == Lesson:
                return LessonSchema(**kwargs)
            elif type_of_lesson == RepeatedLesson:
                return RepeatedLessonSchema(**kwargs)
            else:
                return None
        return dynamic_schema

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(ClassSession,
                                             data.get('class_session_id'))
        self.validate_item_existence_with_id(Address,
                                             data.get('location_id'))


class RepeatedLessonSchema(LessonSchema):
    __model__ = RepeatedLesson
    start_at = fields.DateTime()
    duration = fields.Integer(validate=validate.Range(min=0))
    template_lesson_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    index_of_rep = fields.Integer(
        required=True,
        validate=validate.Range(min=0),
    )
    template_lesson = fields.Nested(
        TemplateLessonSchema,
        only=['id', '_type', 'time_slot', 'location'],
        dump_only=True,
    )

    @validates_schema
    def validate_template_lesson_id(self, data):
        self.validate_item_existence_with_id(TemplateLesson,
                                             data.get('template_lesson_id'))


template_lesson_schema = TemplateLessonSchema()
template_lessons_schema = TemplateLessonSchema(many=True)
template_lesson_patch_schema = TemplateLessonSchema(
    exclude=['class_session_id'])

lesson_schema = LessonSchema()
lessons_schema = LessonSchema(many=True)
lesson_patch_schema = LessonSchema(
    exclude=['class_session_id'])

repeated_lesson_schema = RepeatedLessonSchema()
repeated_lessons_schema = RepeatedLessonSchema(many=True)
repeated_lesson_patch_schema = RepeatedLessonSchema(
    exclude=['class_session_id', 'template_lesson_id'])


class TemplateLessonResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            TemplateLesson, template_lesson_schema, id)

    def patch(self, id):
        template_lesson = self.get_resource_with_ids(TemplateLesson, id)
        json_data = request.get_json()
        try:
            data = template_lesson_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            template_lesson.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = template_lesson_schema.dump(TemplateLesson.get_with_id(
            template_lesson.id))
        return jsonify({APIConst.MESSAGE: 'updated template lesson {}'.format(
            id), APIConst.DATA: result})


class TemplateLessonCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(TemplateLesson,
                                             template_lesson_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = template_lesson_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        template_lesson = TemplateLesson.create(**data)
        result = template_lesson_schema.dump(template_lesson)
        return jsonify(
            {APIConst.MESSAGE: 'created new template lesson',
             APIConst.DATA: result})


class LessonResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Lesson, LessonSchema.make_dynamic_schema(), id)

    def patch(self, id):
        lesson = self.get_resource_with_ids(Lesson, id)
        json_data = request.get_json()
        try:
            data = lesson_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            lesson.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = lesson_schema.dump(Lesson.get_with_id(
            lesson.id))
        return jsonify({APIConst.MESSAGE: 'updated lesson {}'.format(
            id), APIConst.DATA: result})


class LessonCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids=None, cs_id=None):
        if ids is not None:
            return self.response_to_get_with_ids(
                Lesson, LessonSchema.make_dynamic_schema(), ids)
        elif cs_id is not None:
            return self.response_to_get_with_keyvalue_dict(
                Lesson, LessonSchema.make_dynamic_schema(),
                {'class_session_id': cs_id})
        else:
            raise RequestException()


    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = lesson_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        lesson = Lesson.create(**data)
        result = lesson_schema.dump(lesson)
        return jsonify(
            {APIConst.MESSAGE: 'created new lesson',
             APIConst.DATA: result})


class RepeatedLessonResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            RepeatedLesson, repeated_lesson_schema, id)

    def patch(self, id):
        repeated_lesson = self.get_resource_with_ids(RepeatedLesson, id)
        json_data = request.get_json()
        try:
            data = repeated_lesson_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            repeated_lesson.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = repeated_lesson_schema.dump(RepeatedLesson.get_with_id(
            repeated_lesson.id))
        return jsonify({APIConst.MESSAGE: 'updated repeated lesson {}'.format(
            id), APIConst.DATA: result})


class RepeatedLessonCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(RepeatedLesson,
                                             repeated_lesson_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = repeated_lesson_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        repeated_lesson = RepeatedLesson.create(**data)
        result = repeated_lesson_schema.dump(repeated_lesson)
        return jsonify(
            {APIConst.MESSAGE: 'created new repeated lesson',
             APIConst.DATA: result})


template_lesson_view = TemplateLessonResource.as_view('template_lesson_api')
template_lesson_collection_view = TemplateLessonCollectionResource.as_view(
    'template_lesson_collection_api')
bp.add_url_rule('/template-lessons/<int:id>',
                view_func=template_lesson_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/template-lessons/<int_list:ids>',
                view_func=template_lesson_collection_view,
                methods=['GET'])
bp.add_url_rule('/template-lessons',
                view_func=template_lesson_collection_view,
                methods=['GET', 'POST'])


lesson_view = LessonResource.as_view('lesson_api')
lesson_collection_view = LessonCollectionResource.as_view(
    'lesson_collection_api')
bp.add_url_rule('/lessons/<int:id>',
                view_func=lesson_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/lessons/<int_list:ids>',
                view_func=lesson_collection_view,
                methods=['GET'])
bp.add_url_rule('/lessons',
                view_func=lesson_collection_view,
                methods=['GET', 'POST'])
bp.add_url_rule('/class-sessions/<int:cs_id>/lessons',
                view_func=lesson_collection_view,
                methods=['GET'])


repeated_lesson_view = RepeatedLessonResource.as_view('repeated_lesson_api')
repeated_lesson_collection_view = RepeatedLessonCollectionResource.as_view(
    'repeated_lesson_collection_api')
bp.add_url_rule('/repeated-lessons/<int:id>',
                view_func=repeated_lesson_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/repeated-lessons/<int_list:ids>',
                view_func=repeated_lesson_collection_view,
                methods=['GET'])
bp.add_url_rule('/repeated-lessons',
                view_func=repeated_lesson_collection_view,
                methods=['GET', 'POST'])
