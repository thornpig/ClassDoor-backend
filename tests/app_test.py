import unittest
import json
import sys_path_for_test
from app import create_app, db
from app.config import TestConfig


class APPTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app.testing = True
        self.test_client = self.app.test_client()
        self.db = db
        with self.app.app_context():
            self.db.create_all()

    def tearDown(self):
        self.db.session.remove()



