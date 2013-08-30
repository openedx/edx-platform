"""


verify_student/start?course_id=MITx/6.002x/2013_Spring # create
              /upload_face?course_id=MITx/6.002x/2013_Spring
              /upload_photo_id
              /confirm # mark_ready()

 ---> To Payment

"""
import urllib

from django.test import TestCase
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory


class StartView(TestCase):

    def start_url(course_id=""):
        return "/verify_student/{0}".format(urllib.quote(course_id))

    def test_start_new_verification(self):
        """
        Test the case where the user has no pending `PhotoVerficiationAttempts`,
        but is just starting their first.
        """
        user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def must_be_logged_in(self):
        self.assertHttpForbidden(self.client.get(self.start_url()))

