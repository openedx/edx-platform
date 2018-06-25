"""
Unit test module covering utils module
"""
from datetime import date, datetime
import ddt
import pytz
from django.contrib.auth.models import User
from django.test import TestCase

from lms.djangoapps.learner_dashboard import utils
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from student.models import UserProfile


@ddt.ddt
class TestUtils(TestCase):
    """
    The test case class covering the all the utils functions
    """
    shard = 4

    @ddt.data('path1/', '/path1/path2/', '/', '')
    def test_strip_course_id(self, path):
        """
        Test to make sure the function 'strip_course_id'
        handles various url input
        """
        actual = utils.strip_course_id(path + unicode(utils.FAKE_COURSE_KEY))
        self.assertEqual(actual, path)


class DisclaimerIncompleteFieldsTestCase(TestCase):
    """
    Test cases to display or not the reminder alert if a user
    has left some required fields in blank after n days.
    """

    def setUp(self):
        self.user = User.objects.create(
            username='my_self_user',
            date_joined=date(2016, 3, 1)
        )
        self.user_profile = UserProfile.objects.create(
            user_id=self.user.id,
            year_of_birth=1989
        )

    @with_site_configuration(configuration={"DAYS_PASSED_TO_ALERT_PROFILE_INCOMPLETION": 5})
    @with_site_configuration(configuration={"FIELDS_TO_CHECK_PROFILE_COMPLETION": ['gender', 'city', 'year_of_birth']})
    def test_showing_alert(self):
        """
        Test the case when the alert should be displayed
        """
        display_alert = utils.display_incomplete_profile_notification(self.user_profile)
        return self.assertEqual(display_alert, True)

    @with_site_configuration(configuration={"DAYS_PASSED_TO_ALERT_PROFILE_INCOMPLETION": 10})
    @with_site_configuration(configuration={"FIELDS_TO_CHECK_PROFILE_COMPLETION": ['year_of_birth']})
    def test_not_showing_alert(self):
        """
        Test the case when the alert should not be displayed
        """
        display_alert = utils.display_incomplete_profile_notification(self.user_profile)
        return self.assertEqual(display_alert, False)

    @with_site_configuration(configuration={"DAYS_PASSED_TO_ALERT_PROFILE_INCOMPLETION": 5})
    @with_site_configuration(configuration={"FIELDS_TO_CHECK_PROFILE_COMPLETION": []})
    def test_not_showing_alert_no_fields(self):
        """
        Test a case when the alert should not be displayed.
        """
        display_alert = utils.display_incomplete_profile_notification(self.user_profile)
        return self.assertEqual(display_alert, False)

    @with_site_configuration(configuration={"DAYS_PASSED_TO_ALERT_PROFILE_INCOMPLETION": 5})
    @with_site_configuration(configuration={"FIELDS_TO_CHECK_PROFILE_COMPLETION": []})
    def test_not_showing_alert_invalid_period(self):
        """
        Test a case when the alert should not be displayed.
        """
        current = datetime.now(pytz.utc)
        User.objects.filter(username='my_self_user').update(date_joined=current)
        display_alert = utils.display_incomplete_profile_notification(self.user_profile)
        return self.assertEqual(display_alert, False)
