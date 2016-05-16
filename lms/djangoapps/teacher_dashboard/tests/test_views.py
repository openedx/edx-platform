"""
Python tests for Teacher Dashboard views
./manage.py lms test --verbosity=1 lms/djangoapps/teacher_dashboard   --traceback --settings=labster_test
"""

import json
from mock import patch
from ddt import ddt, data

from django.test.client import Client
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from ccx.tests.factories import CcxFactory
from ccx_keys.locator import CCXLocator
from ccx.overrides import override_field_for_ccx
from student.roles import CourseCcxCoachRole
from student.tests.factories import UserFactory


TEST_DATA = json.dumps([{'display_name': 'test'}])


@ddt
class TeacherDashboardViewsTests(ModuleStoreTestCase):
    """
    All tests for the views.py file
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(TeacherDashboardViewsTests, self).setUp()

        self.client = Client()
        self.consumer_keys = ['123', '789']
        self.lti_passports = self.make_lti_passports(self.consumer_keys)
        self.course = CourseFactory.create(
            enable_ccx=True,
            display_name='Test Course', lti_passports=self.lti_passports
        )
        # Create instructor account
        self.user = UserFactory.create()
        self.make_coach()
        self.ccx = self.make_ccx()
        self.ccx_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)
        self.view_url = reverse('teacher_dashboard.views.teacher_dahsboard_handler', args=[unicode(self.course.id)])
        self.client.login(username=self.user.username, password="test")

    def make_lti_passports(self, consumer_keys):
        """
        Create lti passports.
        """
        return [
            ':'.join(['TEST-' + str(i), k, '__secret_key__'])
            for i, k in enumerate(consumer_keys)
        ]

    def make_coach(self):
        """
        Create coach user.
        """
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.user)

    def make_ccx(self):
        """
        Create ccx.
        """
        ccx = CcxFactory(course_id=self.course.id, coach=self.user)
        return ccx

    def test_student_cannot_see_teacher_dashboard(self):
        """
        Asserts that an unauthenticated user cannot access Teacher Dashboard.
        """
        student = UserFactory.create()
        student_user = Client()
        self.client.login(username=student.username, password="test")
        url = reverse('teacher_dashboard.views.dashboard_view', args=[self.course.id])
        response = student_user.get(url)
        self.assertEquals(response.status_code, 302)

    def test_unauthenticated_teacher_view(self):
        """
        Asserts that an unauthenticated user cannot access Teacher Dashboard.
        """
        anon_user = Client()
        url = reverse('teacher_dashboard.views.dashboard_view', args=[self.course.id])
        response = anon_user.get(url)
        self.assertEquals(response.status_code, 302)

    def test_authenticated_teacher_view(self):
        """
        Asserts that an authenticated user can see Teacher Dashboard.
        """
        for course_id in (self.course.id, self.ccx_key):
            url = reverse('teacher_dashboard.views.dashboard_view', args=[self.course.id])
            response = self.client.get(url, follow=True)
            self.assertEquals(response.status_code, 200)
            self.assertIn('teacher-dashboard', response.content)

    @data(
        {'type': 'licenses'},
        {'type': 'simulations', 'license': 'LICENSE'},
        {'type': 'students', 'license': 'LICENSE', 'simulation': 'SIMULATION'},
        {'type': 'attempts', 'license': 'LICENSE', 'simulation': 'SIMULATION'},
    )
    def test_unautneticated_api_callbacks(self, data):
        """
        Asserts that an anonymous user cannot use Teacher Dashboard API.
        """
        anon_user = Client()
        response = anon_user.post(self.view_url, data=data)
        self.assertEquals(response.status_code, 302)

    @data(
        {'type': 'licenses'},
        {'type': 'simulations', 'license': 'LICENSE'},
        {'type': 'students', 'license': 'LICENSE', 'simulation': 'SIMULATION'},
    )
    @patch('teacher_dashboard.views._send_request')
    def test_api_calls(self, data, mock_send_request):
        """
        Asserts that any attempts to api returns 200 with correct content.
        """
        mock_send_request.return_value = TEST_DATA

        response = self.client.post(self.view_url, data=data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, TEST_DATA)
        self.assertEquals(response["Content-Type"], "application/json")

    @patch('teacher_dashboard.views._send_request')
    def test_api_csv_call(self, mock_send_request):
        """
        Asserts that any attempts to `attempts_api_call` api returns 200 with correct content.
        """
        mock_send_request.return_value = TEST_DATA

        response = self.client.get(self.view_url, {
            'type': 'attempts',
            'license': 'LICENSE',
            'simulation': 'SIMULATION',
        })
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, TEST_DATA)
        self.assertEquals(response["Content-Type"], "text/csv")
        expected = 'attachment; filename="{}-summary.csv"'.format(slugify(self.course.id))
        self.assertEquals(response["Content-Disposition"], expected)

    @patch('teacher_dashboard.views._send_request')
    def test_api_license_sends_correct_consumer_keys(self, mock_send_request):
        """
        Asserts that `licenses_api_call` sends correct data to API.
        """
        response = self.client.post(self.view_url, data={'type': 'licenses'})

        mock_send_request.assert_called_with(
            settings.LABSTER_ENDPOINTS.get('licenses'),
            method="POST",
            data=json.dumps({"consumer_keys": self.consumer_keys}),
        )

        ccx_consumer_keys = ['__CCX_KEY_1__']
        ccx_passports = self.make_lti_passports(ccx_consumer_keys)

        # Apply new lti passports to CCX.
        override_field_for_ccx(self.ccx, self.course, 'lti_passports', ccx_passports)

        url = reverse(
            'teacher_dashboard.views.teacher_dahsboard_handler', args=[self.ccx_key]
        )
        response = self.client.post(url, data={'type': 'licenses'})

        mock_send_request.assert_called_with(
            settings.LABSTER_ENDPOINTS.get('licenses'),
            method="POST",
            data=json.dumps({"consumer_keys": ccx_consumer_keys}),
        )
