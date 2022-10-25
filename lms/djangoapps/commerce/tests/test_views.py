""" Tests for commerce views. """

from common.djangoapps.student.tests.factories import UserFactory


class UserMixin:
    """ Mixin for tests involving users. """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def _login(self):
        """ Log into LMS. """
        self.client.login(username=self.user.username, password='test')
