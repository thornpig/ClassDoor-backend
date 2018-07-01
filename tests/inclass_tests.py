import unittest
from datetime import datetime
import os
import sys
import inspect
import json
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from app import create_app, db
from app.config import TestConfig
from app.models import (
    RepeatOptions, TimeSlot, Schedule,
    Lesson, TemplateLesson, Class, ClassSession, RepeatedLesson,
    Person, User, Dependent, Enrollment,
    Organization, OrganizationPersonAssociation,
    Notification, NotificationDelivery, Address
)


def print_json(json_data):
    print(json.dumps(json.loads(json_data), sort_keys=True,
                     indent=4, separators=(',', ': ')))



class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.test_client = self.app.test_client()
        self.db = db
        with self.app.app_context():
            self.db.create_all()

    def tearDown(self):
        self.db.session.remove()

    def test_repeat_option(self):
        dt = datetime(2018, 12, 31, 23, 59, 59)
        rep_dt = RepeatOptions.DAILY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2019, 1, 1, 23, 59, 59)

        dt = datetime(2018, 2, 28, 23, 59, 59)
        rep_dt = RepeatOptions.DAILY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2018, 3, 1, 23, 59, 59)

        dt = datetime(2018, 2, 25, 23, 59, 59)
        rep_dt = RepeatOptions.DAILY.get_repeat_datetime(dt, 4)
        assert rep_dt == datetime(2018, 3, 1, 23, 59, 59)

        dt = datetime(2018, 11, 30, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2018, 12, 30, 23, 59, 59)

        dt = datetime(2018, 1, 30, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 11)
        assert rep_dt == datetime(2018, 12, 30, 23, 59, 59)

        dt = datetime(2018, 12, 31, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2019, 1, 31, 23, 59, 59)

        dt = datetime(2018, 5, 31, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 8)
        assert rep_dt == datetime(2019, 1, 31, 23, 59, 59)

        dt = datetime(2018, 1, 31, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2018, 2, 28, 23, 59, 59)

        dt = datetime(2017, 8, 31, 23, 59, 59)
        rep_dt = RepeatOptions.MONTHLY.get_repeat_datetime(dt, 6)
        assert rep_dt == datetime(2018, 2, 28, 23, 59, 59)

        dt = datetime(2016, 2, 29, 23, 59, 59)
        rep_dt = RepeatOptions.YEARLY.get_repeat_datetime(dt, 1)
        assert rep_dt == datetime(2017, 2, 28, 23, 59, 59)

        dt = datetime(2016, 2, 29, 23, 59, 59)
        rep_dt = RepeatOptions.YEARLY.get_repeat_datetime(dt, 3)
        assert rep_dt == datetime(2019, 2, 28, 23, 59, 59)

        dt = datetime(2000, 2, 29, 23, 59, 59)
        rep_dt = RepeatOptions.YEARLY.get_repeat_datetime(dt, 4)
        assert rep_dt == datetime(2004, 2, 29, 23, 59, 59)

    def test_schedule(self):
        with self.app.app_context():
            ts0 = TimeSlot(start_at=datetime(2018, 2, 27, 11, 59, 59),
                           duration=30)
            ts1 = TimeSlot(start_at=datetime(2018, 2, 28, 11, 59, 59),
                           duration=60)
            end_at = datetime(2018, 3, 14, 9, 59, 59)
            schedule = Schedule(repeat_option=RepeatOptions.WEEKLY,
                                repeat_end_at=end_at,
                                base_time_slots=[ts1, ts0])
            self.db.session.add(schedule)
            self.db.session.commit()

            expected_slots = [
                RepeatTimeSlot(base_time_slot=ts0, repeat_num=0,
                               repeat_option=RepeatOptions.WEEKLY),
                RepeatTimeSlot(base_time_slot=ts1, repeat_num=0,
                               repeat_option=RepeatOptions.WEEKLY),
                RepeatTimeSlot(base_time_slot=ts0, repeat_num=1,
                               repeat_option=RepeatOptions.WEEKLY),
                RepeatTimeSlot(base_time_slot=ts1, repeat_num=1,
                               repeat_option=RepeatOptions.WEEKLY),
                RepeatTimeSlot(base_time_slot=ts0, repeat_num=2,
                               repeat_option=RepeatOptions.WEEKLY),
            ]
            # for rts in expected_slots:
            #     rts._start_at = rts.start_at

            calculated_slots = schedule.get_repeat_time_slots()
            print(calculated_slots)

            assert len(calculated_slots) == len(expected_slots)
            for (ts, exp_ts) in zip(calculated_slots, expected_slots):
                assert (ts.start_at == exp_ts.start_at and
                        ts.base_time_slot.duration ==
                        exp_ts.base_time_slot.duration)

            schedule.repeat_time_slots = expected_slots
            db.session.add(schedule)
            db.session.commit()
            # print(expected_slots[0].start_at, expected_slots[1].start_at)
            # print(schedule.repeat_time_slots[0].start_at,
            #       schedule.repeat_time_slots[1].start_at)

            schedule.repeat_time_slots[0].repeat_num = 10
            for ts in schedule.repeat_time_slots:
                print(ts.start_at)
            db.session.add(schedule.repeat_time_slots[0])
            db.session.commit()
            for ts in schedule.repeat_time_slots:
                print(ts.start_at)

    def test_person(self):
        with self.app.app_context():

            p0 = Person(first_name='zack', last_name='zhu')
            d0 = Dependent(first_name='adela', last_name='zhu')

            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)
            db.session.add(u0)
            db.session.commit()

    def test_organization(self):
        with self.app.app_context():
            p0 = Person(first_name='zack', last_name='zhu')
            d0 = Dependent(first_name='adela', last_name='zhu')

            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            u0.dependents.append(d0)
            # db.session.add(u0)
            # db.session.commit()

            org0 = Organization(name='Iceland', creator=u0)
            op0 = OrganizationPersonAssociation(
                organization=org0, associated_person=p0)
            op1 = OrganizationPersonAssociation(
                organization=org0, associated_person=u0)
            org0.organization_associations.append(op0)
            org0.organization_associations.append(op1)
            db.session.add(org0)
            db.session.commit()
            print(org0.organization_associations[0].associated_person)
            print(org0.organization_associations[1].associated_person)
            print(u0.organization_associations[0].organization)
            print(p0.organization_associations[0].organization)





    def test_class(self):
        with self.app.app_context():
            u0 = User(username='thornpig', email='zack@gmail.com',
                      first_name='zack', last_name='zhu')
            c0 = Class(title='swimming class')
            u0.created_classes.append(c0)
            db.session.add(u0)
            db.session.commit()
            assert c0.creator == u0

            cs0 = ClassSession(class_id=c0.id, creator_id=u0.id)
            ts0 = TimeSlot(start_at=datetime(2018, 2, 27, 11, 59, 59),
                           duration=30)
            ts1 = TimeSlot(start_at=datetime(2018, 2, 28, 11, 59, 59),
                           duration=60)
            end_at = datetime(2018, 3, 14, 9, 59, 59)
            sch0 = Schedule(repeat_option=RepeatOptions.WEEKLY,
                            repeat_end_at=end_at,
                            base_time_slots=[ts0, ts1])
            cs0.schedule = sch0
            self.db.session.add(cs0)
            self.db.session.commit()

            tl0 = TemplateLesson(class_session_id=cs0.id,
                                 time_slot=ts0
                                 )
            tl1 = TemplateLesson(class_session_id=cs0.id,
                                 time_slot=ts1
                                 )
            cs0.template_lessons = [tl0, tl1]
            lessons = cs0.create_lessons()
            # db.session.add_all(lessons)
            # db.session.commit()
            l0 = Lesson(class_session=cs0)

            [cs0.lessons.append(l) for l in lessons]
            cs0.lessons.append(l0)
            print(cs0.lessons.all())
            self.db.session.add(cs0)
            self.db.session.commit()

            print(cs0.lessons.all())


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

        rp = self.test_client.get('/api/v1/users/5')
        print_json(rp.data)


if __name__ == '__main__':
    unittest.main()

