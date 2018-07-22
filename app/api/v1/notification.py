from flask import request, g, abort, jsonify
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from marshmallow import (Schema, fields, validate, ValidationError,
                         validates_schema)
from app.errors.request_exception import RequestException
from app.models import (APIConst, Person, User, Notification,
                        NotificationDelivery)
from . import bp
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin


class NotificationDeliverySchema(BaseSchemaMixin,
                                 TimestampSchemaMixin, Schema):
    __model__ = NotificationDelivery
    notification_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    receiver_id = fields.Integer(required=True, validate=validate.Range(min=1))
    delivered_at = fields.DateTime(dump_only=True)
    notification = fields.Nested(
        'NotificationSchema',
        only=['id', '_type', 'sender_id', 'content'],
        dump_only=True,
    )
    reveiver = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        dump_only=True,
    )

    @validates_schema
    def validate_related_ids(self, data):
        self.validate_item_existence_with_id(Notification,
                                             data.get('notification_id'))
        self.validate_item_existence_with_id(Person,
                                             data.get('receiver_id'))


class NotificationSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Notification
    content = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200),
    )
    sender_id = fields.Integer(required=True, validate=validate.Range(min=1))
    deliveries = fields.Nested(
        NotificationDeliverySchema,
        only=['id', '_type', 'notification_id', 'receiver_id', 'delivered_at'],
        many=True,
        dump_only=True,
    )
    sender = fields.Nested(
        'PersonSchema',
        only=['id', '_type', 'first_name', 'last_name'],
        dump_only=True,
    )

    @validates_schema
    def validate_sender_id(self, data):
        self.validate_item_existence_with_id(Person,
                                             data.get('sender_id'))


notif_delivery_schema = NotificationDeliverySchema()
notif_deliveries_schema = NotificationDeliverySchema(many=True)
notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)


class NotifDeliveryResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            NotificationDelivery, notif_delivery_schema, id)


class NotifDeliveryCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            NotificationDelivery, notif_delivery_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = notif_delivery_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        delivery = NotificationDelivery.create(**data)
        result = notif_delivery_schema.dump(delivery)
        response = jsonify(
            {APIConst.MESSAGE: 'created new notification delivery',
             APIConst.DATA: result})
        return response


class NotificationResource(BaseMethodViewMixin, MethodView):
    def get(self, id):
        return self.response_to_get_with_ids(
            Notification, notification_schema, id)


class NotificationCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            Notification, notification_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = notification_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        notification = Notification.create(**data)
        result = notification_schema.dump(notification)
        response = jsonify(
            {APIConst.MESSAGE: 'created new notification',
             APIConst.DATA: result})
        return response


notif_delivery_view = NotifDeliveryResource.as_view(
    'notif_delivery_api')
notif_delivery_collection_view = NotifDeliveryCollectionResource.as_view(
    'notif_delivery_collection_api')
bp.add_url_rule('/notif-deliveries/<int:id>',
                view_func=notif_delivery_view,
                methods=['GET'])
bp.add_url_rule('/notif-deliveries/<int_list:ids>',
                view_func=notif_delivery_collection_view,
                methods=['GET'])
bp.add_url_rule('/notif-deliveries',
                view_func=notif_delivery_collection_view,
                methods=['GET', 'POST'])

notification_view = NotificationResource.as_view('notification_api')
notification_collection_view = NotificationCollectionResource.as_view(
    'notification_collection_api')
bp.add_url_rule('/notifications/<int:id>',
                view_func=notification_view,
                methods=['GET'])
bp.add_url_rule('/notifications/<int_list:ids>',
                view_func=notification_collection_view,
                methods=['GET'])
bp.add_url_rule('/notifications',
                view_func=notification_collection_view,
                methods=['GET', 'POST'])
