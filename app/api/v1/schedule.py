from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError, pprint,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import APIConst, TimeSlot, Schedule
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin
from app.models import RepeatOption


class TimeSlotSchema(BaseSchemaMixin, Schema):
    __model__ = TimeSlot
    start_at = fields.DateTime(required=True)
    duration = fields.Integer(required=True, validate=validate.Range(min=0))
    schedule_id = fields.Integer(validate=validate.Range(min=1))

    @validates_schema
    def validate_sender_id(self, data):
        self.validate_item_existence_with_id(Schedule,
                                             data.get('schedule_id'))


class ScheduleSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Schedule
    repeat_option = fields.String(validate=validate.OneOf(
        [str(op) for op in RepeatOption], error='Invalid repeat option'))
    repeat_end_at = fields.DateTime()
    base_time_slots = fields.Nested(TimeSlotSchema, many=True)
    repeat_time_slots = fields.Nested(TimeSlotSchema, many=True)

    def load(self, data, many=None, partial=None):

        de_data = super().load(data, many=many, partial=partial)
        de_data = [de_data] if not many else de_data

        for de_data_item in de_data:
            option_class, option_name = de_data_item[
                'repeat_option'].split('.')
            de_data_item['repeat_option'] = eval(option_class)[option_name]

            base_time_slot_dicts = de_data_item.get('base_time_slots')
            if base_time_slot_dicts is not None:
                base_slots = []
                for base_slot_dict in base_time_slot_dicts:
                    base_slot = TimeSlot.create(commit=False, **base_slot_dict)
                    base_slots.append(base_slot)
                de_data_item['base_time_slots'] = base_slots

            repeat_time_slot_dicts = de_data_item.get('repeat_time_slots', [])
            if repeat_time_slot_dicts is not None:
                repeat_slots = []
                for repeat_slot_dict in repeat_time_slot_dicts:
                    repeat_slot = TimeSlot.create(commit=False,
                                                  **repeat_slot_dict)
                    repeat_slots.append(repeat_slot)
                de_data_item['repeat_time_slots'] = repeat_slots

        return de_data if many else de_data[0]


timeslot_schema = TimeSlotSchema()
timeslots_schema = TimeSlotSchema(many=True)
timeslot_patch_schema = TimeSlotSchema(exclude=['schedule_id'])
schedule_schema = ScheduleSchema()
schedule_patch_schema = ScheduleSchema()


class TimeSlotResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            TimeSlot, timeslot_schema, id)

    def patch(self, id):
        timeslot = self.get_resource_with_ids(TimeSlot, id)
        json_data = request.get_json()
        try:
            data = timeslot_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            timeslot.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = timeslot_schema.dump(TimeSlot.get_with_id(timeslot.id))
        return jsonify({APIConst.MESSAGE: 'updated timeslot {}'.format(id),
                        APIConst.DATA: result})


class TimeSlotCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(TimeSlot, timeslot_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = timeslot_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        timeslot = TimeSlot.create(**data)
        result = timeslot_schema.dump(timeslot)
        return jsonify(
            {APIConst.MESSAGE: 'created new timeslot',
             APIConst.DATA: result})


class ScheduleResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Schedule, schedule_schema, id)

    def patch(self, id):
        schedule = self.get_resource_with_ids(Schedule, id)
        json_data = request.get_json()
        try:
            data = schedule_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            schedule.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = schedule_schema.dump(Schedule.get_with_id(schedule.id))
        return jsonify({APIConst.MESSAGE: 'updated schedule {}'.format(id),
                        APIConst.DATA: result})


class ScheduleCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(Schedule, schedule_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = schedule_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)

        schedule = Schedule.create(**data)
        result = schedule_schema.dump(schedule)
        return jsonify(
            {APIConst.MESSAGE: 'created new schedule',
             APIConst.DATA: result})


timeslot_view = TimeSlotResource.as_view('timeslot_api')
timeslot_collection_view = TimeSlotCollectionResource.as_view(
    'timeslot_collection_api')
bp.add_url_rule('/timeslots/<int:id>',
                view_func=timeslot_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/timeslots/<int_list:ids>',
                view_func=timeslot_collection_view,
                methods=['GET'])
bp.add_url_rule('/timeslots',
                view_func=timeslot_collection_view,
                methods=['GET', 'POST'])


schedule_view = ScheduleResource.as_view('schedule_api')
schedule_collection_view = ScheduleCollectionResource.as_view(
    'schedule_collection_api')
bp.add_url_rule('/schedules/<int:id>',
                view_func=schedule_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/schedules/<int_list:ids>',
                view_func=schedule_collection_view,
                methods=['GET'])
bp.add_url_rule('/schedules',
                view_func=schedule_collection_view,
                methods=['GET', 'POST'])
