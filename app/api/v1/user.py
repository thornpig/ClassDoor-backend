from flask import request, g, abort, jsonify
from flask.views import MethodView
from marshmallow import (Schema, fields, validate, ValidationError,
                         validates_schema)
from app.errors import RequestException
from app.models import APIConst, User, Person, Dependent
from .schema_mixins import BaseSchemaMixin, TimestampSchemaMixin
from .method_view_mixins import BaseMethodViewMixin
from . import bp


class PersonSchema(BaseSchemaMixin, TimestampSchemaMixin, Schema):
    __model__ = Person
    first_name = fields.String(required=True, validate=validate.Length(
        min=1, max=30))
    last_name = fields.String(required=True, validate=validate.Length(
        min=1, max=30))
    organization_person_associations = fields.Nested(
        'OrganizationPersonSchema',
        only=['id', '_type', 'organization_id', 'associated_person_id',
              "initiator_id", 'terminated'],
        many=True,
        dump_only=True,
    )
    notification_deliveries = fields.Nested(
        'NotificationDeliverySchema',
        only=['id', '_type', 'delivered_at', 'notification_id', 'receiver_id'],
        many=True,
        dump_only=True,
    )
    instructed_lessons = fields.Nested(
        'LessonSchema',
        only=['id', '_type', 'class_session_id'],
        many=True,
        dump_only=True,
    )
    visiting_lessons = fields.Nested(
        'LessonSchema',
        only=['id', '_type', 'class_session_id'],
        many=True,
        dump_only=True,
    )
    enrollments = fields.Nested(
        'EnrollmentSchema',
        only=['id', '_type', 'enrolled_person_id', 'initiator_id',
              'terminated', 'class_session_id'],
        many=True,
        dump_only=True,
    )

    @staticmethod
    def make_dynamic_schema(**kwargs):
        def dynamic_schema(person):
            type_of_person = type(person)
            if type_of_person == Person:
                return PersonSchema(**kwargs)
            elif type_of_person == User:
                return UserSchema(**kwargs)
            elif type_of_person == Dependent:
                return DependentSchema(**kwargs)
            else:
                return None
        return dynamic_schema


class DependentSchema(PersonSchema):
    __model__ = Dependent
    dependency_id = fields.Integer(required=True,
                                   validate=validate.Range(min=1))

    @validates_schema
    def validate_creator_id(self, data):
        self.validate_item_existence_with_id(User, data.get('dependency_id'))


class UserSchema(PersonSchema):
    __model__ = User
    username = fields.String(required=True, validate=validate.Length(
        min=1, max=30))
    email = fields.String(required=True, validate=validate.Email())
    dependents = fields.Nested(
        DependentSchema,
        only=['id', '_type', 'first_name', 'last_name', 'dependency_id'],
        many=True,
        dump_only=True,
    )
    created_classes = fields.Nested(
        'ClassSchema',
        only=['id', '_type', 'title', 'duration', 'description', 'creator_id',
              'num_of_lessons_per_session', 'capacity'],
        many=True,
        dump_only=True,
    )
    created_organizations = fields.Nested(
        'OrganizationSchema',
        only=['id', '_type', 'name', 'creator_id'],
        many=True,
        dump_only=True,
    )

    #  @validates_schema
    #  def validate_username_uniqueness(self, data):
    #      username = data.get('username')
    #      if username is None:
    #          return
    #      if User.get_with_username(username) is not None:
    #          raise ValidationError('username {} has been taken'.format(
    #              username))

    #  @validates_schema
    #  def validate_email_uniqueness(self, data):
    #      email = data.get('email')
    #      if email is None:
    #          return
    #      users = User.get_items_with_keyvalue_dict({'email': email})
    #      if len(users) > 0:
    #          raise ValidationError('email {} has been taken'.format(
    #              email))


user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_patch_schema = UserSchema(exclude=['username'])
dependent_schema = DependentSchema()
dependents_schema = DependentSchema(many=True)
dependent_patch_schema = DependentSchema()


class PersonResource(BaseMethodViewMixin, MethodView):

    def get(self, id):
        return self.response_to_get_with_ids(
            Person, PersonSchema.make_dynamic_schema(), id)


class PersonCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(
            Person, PersonSchema.make_dynamic_schema(), ids)


class DependentResource(BaseMethodViewMixin, MethodView):

    def get(self, id):
        return self.response_to_get_with_ids(
            Dependent, dependent_schema, id)

    def patch(self, id):
        dependent = self.get_resource_with_ids(Dependent, id)
        json_data = request.get_json()
        try:
            data = dependent_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            dependent.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = dependent_schema.dump(Dependent.get_with_id(dependent.id))
        response = jsonify({
            APIConst.MESSAGE: 'updated dependent {}'.format(id),
            APIConst.DATA: result})
        return response


class DependentCollectionResource(BaseMethodViewMixin, MethodView):

    def get(self, ids):
        return self.response_to_get_with_ids(Dependent, dependent_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = dependent_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        dependent = Dependent.create(**data)
        result = dependent_schema.dump(dependent)
        response = jsonify({APIConst.MESSAGE: 'created new dependent',
                            APIConst.DATA: result})
        return response


class UserResource(BaseMethodViewMixin, MethodView):

    def get(self, id=None, username=None):
        if id is not None:
            return self.response_to_get_with_ids(User, user_schema, id)
        elif username is not None:
            return self.response_to_get_with_keyvalue_dict(
                User, user_schema, {'username': username}, unique=True)

    def patch(self, id=None, username=None):
        user = None
        if id is not None:
            user = self.get_resource_with_ids(User, id)
        elif username is not None:
            user = self.get_resource_with_keyvalue_dict(User,
                                                        {'username': username},
                                                        unique=True)
        json_data = request.get_json()
        try:
            data = user_patch_schema.load(json_data, partial=True)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        try:
            user.update(**data)
        except Exception as err:
            raise RequestException(
                payload={APIConst.INPUT: json_data}) from err
        result = user_schema.dump(User.get_with_id(user.id))
        response = jsonify({APIConst.MESSAGE: 'updated user',
                            APIConst.DATA: result})
        return response

    def delete(self, id=None, username=None):
        user = None
        if id is not None:
            user = self.get_resource_with_ids(User, id)
        elif username is not None:
            user = self.get_resource_with_keyvalue_dict(User,
                                                        {'username': username},
                                                        unique=True)
        try:
            user.delete()
        except Exception as err:
            raise RequestException("User {} could not be deleted".format(
                user.username), 500)
        response = jsonify({
            APIConst.MESSAGE:
            "User {} has been deleted.".format(user.username)}), 200
        return response


class UserCollectionResource(BaseMethodViewMixin, MethodView):
    def get(self, ids=None):
        return self.response_to_get_with_ids(User, user_schema, ids)

    def post(self):
        json_data = request.get_json()
        if not json_data:
            raise RequestException("No input data", 400)
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            raise RequestException("Invalid input data", 400, err.messages)
        print(data)
        username = data['username']
        if User.get_with_username(username) is not None:
            raise RequestException("username '{}' has been taken".format(
                username), 400)
        else:
            User.create(**data)
            result = user_schema.dump(User.get_with_username(username))
            response = jsonify({
                APIConst.MESSAGE: 'created new user',
                APIConst.DATA: result})
            return response


person_view = PersonResource.as_view('person_api')
person_collection_view = PersonCollectionResource.as_view(
    'person_colection_api')
bp.add_url_rule('/persons/<int:id>',
                view_func=person_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/persons/<int_list:ids>',
                view_func=person_collection_view,
                methods=['GET'])
bp.add_url_rule('/persons',
                view_func=person_collection_view,
                methods=['GET', 'POST'])

dependent_view = DependentResource.as_view('dependent_api')
dependent_collection_view = DependentCollectionResource.as_view(
    'dependent_collection_api')
bp.add_url_rule('/dependents/<int:id>',
                view_func=dependent_view,
                methods=['GET', 'PATCH'])
bp.add_url_rule('/dependents/<int_list:ids>',
                view_func=dependent_collection_view,
                methods=['GET'])
bp.add_url_rule('/dependents',
                view_func=dependent_collection_view,
                methods=['GET', 'POST'])


user_view = UserResource.as_view('user_api')
user_collection_view = UserCollectionResource.as_view('user_collection_api')
bp.add_url_rule('/users/<int:id>',
                view_func=user_view,
                methods=['GET', 'PATCH', 'DELETE'])
bp.add_url_rule('/users/<int_list:ids>',
                view_func=user_collection_view,
                methods=['GET'])
bp.add_url_rule('/users/<username>',
                view_func=user_view,
                methods=['GET', 'PATCH', 'DELETE'])
bp.add_url_rule('/users',
                view_func=user_collection_view,
                methods=['GET', 'POST'])
