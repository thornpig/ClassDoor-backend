from flask import request, g, abort, jsonify
from flask.views import MethodView
from marshmallow import Schema, fields, validate, ValidationError, pprint
from app.models.user import User
from . import bp


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Str(required=True, validate=validate.Email())


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class UserResource(MethodView):
    def get(self, user_id=None, username=None):
        user = None
        if user_id is not None:
            user = User.get_with_id(user_id)
        elif username is not None:
            user = User.get_with_username(username)
        if user is None:
            return jsonify({"message":
                            "User could not be found"}), 400
        result = user_schema.dump(user)

        load_list = request.args.getlist('load_list')
        print(load_list)
        if 'posts' in load_list:
            from .post import posts_schema
            result['posts'] = posts_schema.dump(user.posts.all())
        return jsonify({'user': result})

    def delete(self, user_id=None, username=None):
        user = None
        if user_id is not None:
            user = User.get_with_id(user_id)
        elif username is not None:
            user = User.get_with_username(username)
        if user is None:
            return jsonify({"message":
                            "User to delete could not be found"}), 400
        try:
            user.delete()
            return jsonify({"message": "User {} has been deleted.".format(
                user.username)}), 200
        except Exception as err:
            return jsonify({"message": "User {} could not be deleted".format(
                user.username)}), 500


class UserCollectionResource(MethodView):
    def get(self):
        users = User.query.all()
        result = users_schema.dump(users)
        return jsonify({'users': result})

    def post(self):
        json_data = request.get_json()
        print(json_data)
        if not json_data:
            return jsonify({'message': "No input data"}), 400
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return jsonify(err.messages), 422
        username = data['username']
        email = data['email']
        if User.get_with_username(username) is not None:
            return jsonify({'message': 'username has been taken'}), 400
        else:
            User.create(username=username, email=email)
            result = user_schema.dump(User.get_with_username(username))
            return jsonify({'message': 'created new user',
                            'user': result})


bp.add_url_rule('/users/<int:user_id>',
                view_func=UserResource.as_view('user_resource_id'))
bp.add_url_rule('/users/<username>',
                view_func=UserResource.as_view('user_resource_username'))
bp.add_url_rule('/users/',
                view_func=UserCollectionResource.as_view('users_resource'))
