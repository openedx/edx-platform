""" Tests for student profile views. """

from mock import patch
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
class StudentProfileViewTest(TestCase):
    """ Tests for the student profile views. """

    def test_index(self):
        response = self.client.get(reverse('profile_index'))
        self.assertContains(response, "Student Profile")