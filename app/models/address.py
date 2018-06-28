from .database import db, Model, SurrogatePK


class Address(SurrogatePK, Model):
    __tablename__ = 'address'
    primary_street = db.Column(db.String(100), nullable=False)
    secondary_street = db.Column(db.String(100), default='')
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    zipcode = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return '<Address {} {}, {}, {} {}, {}>'.format(
            self.primary_street, self.secondary_street,
            self.city, self.state, self.zipcode, self.country)

