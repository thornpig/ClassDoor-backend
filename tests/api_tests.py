import unittest
import json
from app_test import APPTestCase
from app import create_app, db
from app.config import TestConfig
from app.models import (
    RepeatOptions, TimeSlot, Schedule,
    Lesson, TemplateLesson, Class, ClassSession, RepeatedLesson,
    Person, User, Dependent, Enrollment,
    Organization, OrganizationPersonAssociation,
    Notification, NotificationDelivery, Address,
)
from app.api.v1 import (
    UserSchema, PersonSchema, DependentSchema,
    # EnrollmentSchema,
)


def print_json(json_data):
    print(json.dumps(json.loads(json_data), sort_keys=True,
                     indent=4, separators=(',', ': ')))


class APITestCase(APPTestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.test_client = self.app.test_client()
        self.db = db
        with self.app.app_context():
            self.db.create_all()

    def tearDown(self):
        self.db.session.remove()

    def test_api_user(self):
        with self.app.app_context():
            d0 = Dependent(first_name='adela', last_name='zhu')

            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)
            self.db.session.add(u0)
            self.db.session.commit()

            u1 = User(username='Adela', email='adela@gmail.com',
                      first_name='adela', last_name='zhu')
            self.db.session.add(u1)
            self.db.session.commit()

        rp = self.test_client.get('/api/v1/users/1')
        print_json(rp.data)


if __name__ == '__main__':
    unittest.main()
