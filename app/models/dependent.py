from .database import db
from .person import Person


class Dependent(Person):
    __tablename__ = 'dependent'
    id = db.Column(db.ForeignKey('person.id'), primary_key=True)
    first_name = db.Column('dp_first_name', db.String(30), nullable=False)
    last_name = db.Column('dp_last_name', db.String(30), nullable=False)
    dependency_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    __table_args__ = (
        db.CheckConstraint(
            db.and_(db.text('length(dp_first_name) > 0'),
                    db.text('length(dp_last_name) > 0'))),
        db.UniqueConstraint(
            'dependency_id', 'dp_first_name', 'dp_last_name',
            name='dependent_name_dependency_id_unique')
    )

    __mapper_args__ = {
        'polymorphic_identity': 'dependent',
    }

