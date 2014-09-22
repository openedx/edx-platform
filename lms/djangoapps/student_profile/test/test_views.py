# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from urllib import urlencode
from mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse

from user_api.api import account as account_api
from user_api.api import profile as profile_api
from student_profile import views as profile_views


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
class StudentProfileViewTest(TestCase):
    """ Tests for the student profile views. """

    USERNAME = u"frank_under-wood"
    PASSWORD = u"ṕáśśẃőŕd"
    EMAIL = u"fŕáńḱ@éxáḿṕĺé.ćőḿ"
    FULL_NAME = u"FɍȺnꝁ ᵾnđɇɍwøøđ"

    def test_index(self):
        response = self.client.get(reverse('profile_index'))
        self.assertContains(response, "Student Profile")

    def test_name_change_handler(self):
        # Create a new user
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Verify that the name on the account is blank
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['full_name'], '')

        # Make a PUT request to change the name on the account
        self.request_factory = RequestFactory()
        # The test client's post method runs urlencode on its data argument 
        # internally if content_type remains unchanged, but this luxury has not been 
        # extended to any of the other methods used to make requests (i.e., put)
        request = self.request_factory.put(
            path= reverse('name_change'), 
            data= urlencode({
                # We can't pass a Unicode object to urlencode, so we encode the Unicode object
                'proposed_name': self.FULL_NAME.encode('utf8')
            }),
            content_type= 'application/x-www-form-urlencoded'
        )
        request.user = User.objects.get(username=self.USERNAME)

        response = profile_views.name_change_handler(request)
        self.assertEquals(response.status_code, 204)

        # Verify that the name on the account has been changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['full_name'], self.FULL_NAME)
