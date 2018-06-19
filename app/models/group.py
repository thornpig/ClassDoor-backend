from datetime import datetime
from app import db


class Class(db.Model):
    classname = db.Column(db.String(64), index=True)
    description = db.Column(db.String(1000))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
