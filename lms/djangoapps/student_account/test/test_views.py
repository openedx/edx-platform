""" Tests for student account views. """

from mock import patch
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
class StudentAccountViewTest(TestCase):
    """ Tests for the student account views. """

    def test_index(self):
        response = self.client.get(reverse('account_index'))
        self.assertContains(response, "Student Account")