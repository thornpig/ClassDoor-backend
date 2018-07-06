import unittest
from datetime import datetime
import json
from app_test import APPTestCase
from app import create_app, db
from app.config import TestConfig
from app.models import (
    RepeatOption, TimeSlot, Schedule,
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
        super().setUp()
        self.create_db_entries()

    def create_db_entries(self):
        with self.app.app_context():
            d0 = Dependent(first_name='adela', last_name='zhu')
            d1 = Dependent(first_name='dudu', last_name='du')
            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents = [d0, d1]
            u1 = User(username='shirly', email='shirly@gmail.com',
                      first_name='shirly', last_name='zheng')

            ts0 = TimeSlot(start_at=datetime(2018, 2, 27, 11, 59, 59),
                           duration=30)
            ts1 = TimeSlot(start_at=datetime(2018, 2, 28, 11, 59, 59),
                           duration=60)
            end_at = datetime(2018, 3, 14, 9, 59, 59)
            schedule = Schedule(repeat_option=RepeatOption.WEEKLY,
                                repeat_end_at=end_at,
                                base_time_slots=[ts1, ts0])
            c0 = Class(creator=u0, title='english class',
                       description='learn english',
                       duration=60)

            addr0 = Address(primary_street='12345 ABC st',
                            city='XYZ',
                            state='FL',
                            zipcode='12345',
                            country='USA',
                            creator=u0)

            cs0 = ClassSession(parent_class=c0, creator=u0, schedule=schedule)

            self.db.session.add_all([u0, u1, schedule, c0, cs0, addr0])
            self.db.session.commit()

            #  tl = TemplateLesson(class_session_id=cs0.id)
            #  self.db.session.add(tl)
            #  self.db.session.commit()



    def test_dynamic_person_schema(self):
        p0 = Person(first_name='Adela', last_name='Zhu')
        u0 = User(username='zackzhu', email='zack@gmail.com',
                  first_name='zack', last_name='zhu')
        d0 = Dependent(first_name='Ada', last_name='adA')

        assert PersonSchema.dynamic_schema(p0) == PersonSchema
        assert PersonSchema.dynamic_schema(u0) == UserSchema
        assert PersonSchema.dynamic_schema(d0) == DependentSchema

        assert type(PersonSchema.dynamic_schema(d0)(
            many=True)) == DependentSchema

    def test_user(self):
        rp = self.test_client.get('/api/v1/users/1')
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/users',
            data=json.dumps(dict(username='pig',
                            email='pig@gmail.com',
                            first_name='pig', last_name='pig')),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/users/1',
            data=json.dumps(
                dict(
                    email='zerg@gmail.com',
                    first_name='pig', last_name='pig'
                )
            ),
            content_type='application/json',

        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/persons/1,2,3,4,5')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/dependents/3,4')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/users/1,2,5')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/persons/1')
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/dependents',
            data=json.dumps(dict(
                dependency_id=5, first_name='lulu', last_name='gaga')),
            content_type='application/json',
        )
        print_json(rp.data)

    def test_address(self):
        with self.app.app_context():
            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            addr0 = Address(primary_street='12345 ABC st',
                            city='XYZ',
                            state='FL',
                            zipcode='12345',
                            country='USA',
                            creator=u0)
            db.session.add(addr0)
            db.session.commit()

        rp = self.test_client.get('/api/v1/addresses/1')
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/addresses',
            data=json.dumps(
                dict(
                    creator_id=2,
                    primary_street='789 WWWW LN',
                    city='XYZ',
                    state='FL',
                    zipcode='12345',
                    country='USA'
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/addresses',
            data=json.dumps(
                dict(
                    creator_id=1,
                    primary_street='789 WWWW LN',
                    city='XYZ',
                    state='FL',
                    zipcode='12345',
                    country='USA'
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/addresses/2',
            data=json.dumps(
                dict(
                    creator_id=2,
                    primary_street='1234 WWWW LN',
                    secondary_street='APT 123',
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        
    def test_schedule(self):
        with self.app.app_context():
            ts0 = TimeSlot(start_at=datetime(2018, 2, 27, 11, 59, 59),
                           duration=30)
            ts1 = TimeSlot(start_at=datetime(2018, 2, 28, 11, 59, 59),
                           duration=60)
            end_at = datetime(2018, 3, 14, 9, 59, 59)
            schedule = Schedule(repeat_option=RepeatOption.WEEKLY,
                                repeat_end_at=end_at,
                                base_time_slots=[ts1, ts0])
            db.session.add(schedule)
            db.session.commit()

        rp = self.test_client.get('/api/v1/timeslots/1,2')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/schedules/1')
        print_json(rp.data)

        ts2_dict = dict(
            start_at=datetime(2018, 12, 27, 11, 59, 59).isoformat(),
            duration=30)
        ts3_dict = dict(
            start_at=datetime(2018, 12, 28, 11, 59, 59).isoformat(),
            duration=60)
        end_at_str = datetime(2019, 1, 20, 9, 59, 59).isoformat()

        rp = self.test_client.post(
            '/api/v1/schedules',
            data=json.dumps(
                dict(
                    repeat_option=str(RepeatOption.WEEKLY),
                    repeat_end_at=end_at_str,
                    base_time_slots=[ts2_dict, ts3_dict],
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        end_at_str = datetime(2019, 2, 20, 9, 59, 59).isoformat()
        rp = self.test_client.patch(
            '/api/v1/schedules/2',
            data=json.dumps(
                dict(
                    repeat_option=str(RepeatOption.WEEKLY),
                    repeat_end_at=end_at_str,
                    #  base_time_slots=[ts2_dict, ts3_dict],
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)


    def test_organization(self):
        with self.app.app_context():
            p0 = Person(first_name='zack', last_name='zhu')
            d0 = Dependent(first_name='adela', last_name='zhu')

            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)

            org0 = Organization(name='Iceland', creator=u0)
            op0 = OrganizationPersonAssociation(
                organization=org0, associated_person=p0)
            op1 = OrganizationPersonAssociation(
                organization=org0, associated_person=u0)
            org0.organization_person_associations.append(op0)
            org0.organization_person_associations.append(op1)

            org1 = Organization(name='Catsland', creator=u0)
            op2 = OrganizationPersonAssociation(
                organization=org1, associated_person=p0)
            org1.organization_person_associations.append(op2)
            db.session.add_all([org0, org1])
            db.session.commit()

        rp = self.test_client.get('/api/v1/organizations/1,2')
        print_json(rp.data)

        rp = self.test_client.get(
            '/api/v1/org-per-assns/1,2')
        print_json(rp.data)

        with self.app.app_context():
            u1 = User(username='pig', email='pig@gmail.com',
                      first_name='pig', last_name='pig')
            db.session.add(u1)
            db.session.commit()

        rp = self.test_client.post(
            '/api/v1/org-per-assns',
            data=json.dumps(
                dict(
                    organization_id=2,
                    associated_person_id=3,
                    initiator_id=4,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/org-per-assns/4',
            data=json.dumps(
                dict(
                    terminated=True
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/organizations',
            data=json.dumps(
                dict(
                    name='Soccer school',
                    creator_id=4,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/organizations/3',
            data=json.dumps(
                dict(
                    name='Football school'
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

    def test_notification(self):
        with self.app.app_context():
            d0 = Dependent(first_name='adela', last_name='zhu')
            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)
            u1 = User(username='zerg', email='zerg@gmail.com',
                      first_name='zerg', last_name='zerg')
            db.session.add_all([u0, u1])
            db.session.commit()

        rp = self.test_client.post(
            '/api/v1/notifications',
            data=json.dumps(
                dict(
                    content='wa ha ha',
                    sender_id=1
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/notifications',
            data=json.dumps(
                dict(
                    content='have fun',
                    sender_id=2
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/notifications/1,2')
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/notif-deliveries',
            data=json.dumps(
                dict(
                    notification_id=1,
                    receiver_id=3
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/notif-deliveries',
            data=json.dumps(
                dict(
                    notification_id=2,
                    receiver_id=3
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/notif-deliveries/1,2')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/persons/3')
        print_json(rp.data)


    def test_class(self):
        with self.app.app_context():
            d0 = Dependent(first_name='adela', last_name='zhu')
            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)
            u1 = User(username='zerg', email='zerg@gmail.com',
                      first_name='zerg', last_name='zerg')

            ts0 = TimeSlot(start_at=datetime(2018, 2, 27, 11, 59, 59),
                           duration=30)
            ts1 = TimeSlot(start_at=datetime(2018, 2, 28, 11, 59, 59),
                           duration=60)
            end_at = datetime(2018, 3, 14, 9, 59, 59)
            schedule = Schedule(repeat_option=RepeatOption.WEEKLY,
                                repeat_end_at=end_at,
                                base_time_slots=[ts1, ts0])

            db.session.add_all([u0, u1, schedule])
            db.session.commit()

        address_dicts = [
            dict(
                creator_id=1,
                primary_street='789 WWWW LN',
                city='XYZ',
                state='FL',
                zipcode='12345',
                country='USA'
            ),
            dict(
                creator_id=1,
                primary_street='123 ABC LN',
                city='XYZ',
                state='CA',
                zipcode='11111',
                country='CHINA'
            ),
        ]

        rp = self.test_client.post(
            '/api/v1/classes',
            data=json.dumps(
                dict(
                    title='swimming class',
                    description='simply the best',
                    duration=60,
                    num_of_lessons_per_session=10,
                    capacity=2,
                    min_age=5,
                    creator_id=1,
                    locations=address_dicts
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)


        rp = self.test_client.get('/api/v1/classes/1')
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/classes/1',
            data=json.dumps(
                dict(
                    title='swimming class',
                    description='simply the best',
                    duration=60,
                    num_of_lessons_per_session=10,
                    capacity=2,
                    min_age=5,
                    creator_id=1,
                    #  locations=[{'id': 2}]
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/class-sessions',
            data=json.dumps(
                dict(
                    class_id=1,
                    creator_id=1,
                    schedule_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        ts2_dict = dict(
            start_at=datetime(2018, 12, 27, 11, 59, 59).isoformat(),
            duration=30)
        ts3_dict = dict(
            start_at=datetime(2018, 12, 28, 11, 59, 59).isoformat(),
            duration=60)
        end_at_str = datetime(2019, 1, 20, 9, 59, 59).isoformat()

        rp = self.test_client.post(
            '/api/v1/schedules',
            data=json.dumps(
                dict(
                    repeat_option=str(RepeatOption.WEEKLY),
                    repeat_end_at=end_at_str,
                    base_time_slots=[ts2_dict, ts3_dict],
                    )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/class-sessions/1',
            data=json.dumps(
                dict(
                    class_id=2,
                    creator_id=2,
                    schedule_id=2,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)


    def test_lesson(self):
        rp = self.test_client.post(
            '/api/v1/template-lessons',
            data=json.dumps(
                dict(
                    time_slot_id=1,
                    class_session_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        #  with self.app.app_context():
        #      lessons = self.db.session.query(
        #          Lesson).filter_by(class_session_id=1).all()
        #      print(lessons)

        rp = self.test_client.get('/api/v1/class-sessions/1/lessons')
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/template-lessons/1',
            data=json.dumps(
                dict(
                    time_slot_id=2,
                    class_session_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/class-sessions/1/lessons')
        print_json(rp.data)

        with self.app.app_context():
            tl = self.db.session.query(TemplateLesson).get(1)
            tl.class_session_id = None
            self.db.session.add(tl)
            self.db.session.commit()
        rp = self.test_client.get('/api/v1/class-sessions/1/lessons')
        print_json(rp.data)
        exit()

        rp = self.test_client.post(
            '/api/v1/lessons',
            data=json.dumps(
                dict(
                    start_at=datetime(2019, 1, 20, 9, 59, 59).isoformat(),
                    duration=30,
                    class_session_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/lessons/1',
            data=json.dumps(
                dict(
                    start_at=datetime(2019, 6, 20, 9, 59, 59).isoformat(),
                    duration=60,
                    class_session_id=2,
                    location_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/repeated-lessons',
            data=json.dumps(
                dict(
                    template_lesson_id=1,
                    index_of_rep=2,
                    class_session_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/repeated-lessons/2',
            data=json.dumps(
                dict(
                    start_at=datetime(2019, 12, 20, 9, 59, 59).isoformat(),
                    duration=60,
                    class_session_id=2,
                    location_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/class-sessions/1')
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/lessons/1,2')
        print_json(rp.data)




    def test_enrollment(self):
        rp = self.test_client.post(
            '/api/v1/enrollments',
            data=json.dumps(
                dict(
                    enrolled_person_id=1,
                    class_session_id=1,
                    initiator_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.patch(
            '/api/v1/enrollments/1',
            data=json.dumps(
                dict(
                    enrolled_person_id=2,
                    class_session_id=2,
                    initiator_id=2,
                    terminated=True
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.post(
            '/api/v1/enrollments',
            data=json.dumps(
                dict(
                    enrolled_person_id=2,
                    class_session_id=1,
                    initiator_id=1,
                )
            ),
            content_type='application/json',
        )
        print_json(rp.data)

        rp = self.test_client.get('/api/v1/enrollments/1,2')
        print_json(rp.data)


if __name__ == '__main__':
    unittest.main()
