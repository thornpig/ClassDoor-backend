from flask import g, abort, jsonify
from flask.views import MethodView
from marshmallow import Schema, fields, validate, ValidationError, pprint
from app.models.post import Post
from . import bp
from .user import UserSchema


class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    body = fields.Str(required=True, validate=validate.Length(min=1))
    user_id = fields.Int(required=True, validate=validate.Length(min=1))
    timestamp = fields.DateTime(dump_only=True)
    author = fields.Nested(UserSchema, dump_only=True)


post_schema = PostSchema(exclude=['author'])
posts_schema = PostSchema(many=True, exclude=['author'])
post_schema_with_user = PostSchema(exclude=['user_id'])
posts_schema_with_user = PostSchema(many=True, exclude=['user_id'])
