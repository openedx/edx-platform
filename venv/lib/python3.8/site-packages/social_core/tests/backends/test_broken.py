import unittest

from ...backends.base import BaseAuth
from ..models import TestStorage
from ..strategy import TestStrategy


class BrokenBackendAuth(BaseAuth):
    name = 'broken'


class BrokenBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = BrokenBackendAuth(TestStrategy(TestStorage))

    def tearDown(self):
        self.backend = None

    def test_auth_url(self):
        with self.assertRaisesRegex(NotImplementedError,
                                    'Implement in subclass'):
            self.backend.auth_url()

    def test_auth_html(self):
        with self.assertRaisesRegex(NotImplementedError,
                                    'Implement in subclass'):
            self.backend.auth_html()

    def test_auth_complete(self):
        with self.assertRaisesRegex(NotImplementedError,
                                    'Implement in subclass'):
            self.backend.auth_complete()

    def test_get_user_details(self):
        with self.assertRaisesRegex(NotImplementedError,
                                    'Implement in subclass'):
            self.backend.get_user_details(None)
