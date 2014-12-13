"""
Unit tests for masquerade

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

./manage.py lms --settings test test lms/djangoapps/courseware
"""
import json

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.tests.factories import StaffFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from lms.djangoapps.lms_xblock.runtime import quote_slashes
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_GRADED_MODULESTORE


# TODO: the "abtest" node in the sample course "graded" is currently preventing
# it from being successfully loaded in the mongo modulestore.
# Fix this testcase class to not depend on that course, and let it use
# the mocked modulestore instead of the XML.
@override_settings(MODULESTORE=TEST_DATA_MIXED_GRADED_MODULESTORE)
class TestStaffMasqueradeAsStudent(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check for staff being able to masquerade as student.
    """

    def setUp(self):
        # Clear out the modulestores, causing them to reload
        clear_existing_modulestores()
        self.graded_course = modulestore().get_course(SlashSeparatedCourseKey("edX", "graded", "2012_Fall"))

        # Create staff account
        self.staff = StaffFactory(course_key=self.graded_course.id)

        self.logout()
        # self.staff.password is the sha hash but login takes the plain text
        self.login(self.staff.email, 'test')
        self.enroll(self.graded_course)

    def get_cw_section(self):
        url = reverse('courseware_section',
                      kwargs={'course_id': self.graded_course.id.to_deprecated_string(),
                              'chapter': 'GradedChapter',
                              'section': 'Homework1'})

        resp = self.client.get(url)

        print "url ", url
        return resp

    def test_staff_debug_for_staff(self):
        resp = self.get_cw_section()
        sdebug = 'Staff Debug Info'
        print resp.content
        self.assertTrue(sdebug in resp.content)

    def toggle_masquerade(self):
        """
        Toggle masquerade state.
        """
        masq_url = reverse('masquerade-switch', kwargs={'marg': 'toggle'})
        print "masq_url ", masq_url
        resp = self.client.get(masq_url)
        return resp

    def test_no_staff_debug_for_student(self):
        togresp = self.toggle_masquerade()
        print "masq now ", togresp.content
        self.assertEqual(togresp.content, '{"status": "student"}', '')

        resp = self.get_cw_section()
        sdebug = 'Staff Debug Info'

        self.assertFalse(sdebug in resp.content)

    def get_problem(self):
        pun = 'H1P1'
        problem_location = self.graded_course.id.make_usage_key("problem", pun)

        modx_url = reverse('xblock_handler',
                           kwargs={'course_id': self.graded_course.id.to_deprecated_string(),
                                   'usage_id': quote_slashes(problem_location.to_deprecated_string()),
                                   'handler': 'xmodule_handler',
                                   'suffix': 'problem_get'})

        resp = self.client.get(modx_url)

        print "modx_url ", modx_url
        return resp

    def test_showanswer_for_staff(self):
        resp = self.get_problem()
        html = json.loads(resp.content)['html']
        print html
        sabut = '<button class="show"><span class="show-label">Show Answer</span> <span class="sr">Reveal Answer</span></button>'
        self.assertTrue(sabut in html)

    def test_no_showanswer_for_student(self):
        togresp = self.toggle_masquerade()
        print "masq now ", togresp.content
        self.assertEqual(togresp.content, '{"status": "student"}', '')

        resp = self.get_problem()
        html = json.loads(resp.content)['html']
        sabut = '<button class="show"><span class="show-label" aria-hidden="true">Show Answer</span> <span class="sr">Reveal answer above</span></button>'
        self.assertFalse(sabut in html)
