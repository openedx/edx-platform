# -*- coding: utf-8 -*-
""" Tests for student account views. """

from urllib import urlencode
from mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse

from user_api.api import account as account_api
from user_api.api import profile as profile_api
from student_account import views as account_views


@patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
class StudentAccountViewTest(TestCase):
    """ Tests for the student account views. """

    USERNAME = u"heisenberg"
    PASSWORD = u"ḅḷüëṡḳÿ"
    OLD_EMAIL = u"walt@savewalterwhite.com"
    NEW_EMAIL = u"heisenberg@felina.com"

    def test_index(self):
        response = self.client.get(reverse('account_index'))
        self.assertContains(response, "Student Account")

    def test_email_change_request_handler(self):
        # Create a new user
        account_api.create_account(self.USERNAME, self.PASSWORD, self.OLD_EMAIL)

        # Verify that the email associated with the account is unchanged
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

        # Make a PUT request to change the email associated with the account
        self.request_factory = RequestFactory()
        # The test client's post method runs urlencode on its data argument 
        # internally if content_type remains unchanged, but this luxury has not been 
        # extended to any of the other methods used to make requests (i.e., put)
        request = self.request_factory.put(
            path= reverse('email_change_request'), 
            data= urlencode({
                # We can't pass a Unicode object to urlencode, so we encode the Unicode object
                'new-email': self.NEW_EMAIL,
                'password': self.PASSWORD.encode('utf8')
            }),
            content_type= 'application/x-www-form-urlencoded'
        )
        request.user = User.objects.get(username=self.USERNAME)

        response = account_views.email_change_request_handler(request)
        self.assertEquals(response.status_code, 204)

    def email_change_confirmation_handler(self):
        pass
