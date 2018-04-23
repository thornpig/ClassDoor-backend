from . import api
from flask_restful import Resource, reqparse, fields, marshal, marshal_with
from .models.user import User

user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String
}


class UserResource(Resource):




