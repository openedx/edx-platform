"""
Test view handler for rerun (and eventually create)
"""


import datetime

import ddt
import six
from django.test import override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from organizations.api import (
    add_organization,
    get_organization_by_short_name,
    get_course_organizations
)
from organizations.exceptions import InvalidOrganizationException

from cms.djangoapps.contentstore.tests.utils import AjaxEnabledTestClient, parse_json
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.course_module import CourseFields
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class TestCourseListing(ModuleStoreTestCase):
    """
    Unit tests for getting the list of courses for a logged in user
    """
    def setUp(self):
        """
        Add a user and a course
        """
        super(TestCourseListing, self).setUp()
        # create and log in a staff user.
        # create and log in a non-staff user
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password='test')
        self.course_create_rerun_url = reverse('course_handler')
        self.course_start = datetime.datetime.utcnow()
        self.course_end = self.course_start + datetime.timedelta(days=30)
        self.enrollment_start = self.course_start - datetime.timedelta(days=7)
        self.enrollment_end = self.course_end - datetime.timedelta(days=14)
        source_course = CourseFactory.create(
            org='origin',
            number='the_beginning',
            run='first',
            display_name='the one and only',
            start=self.course_start,
            end=self.course_end,
            enrollment_start=self.enrollment_start,
            enrollment_end=self.enrollment_end
        )
        self.source_course_key = source_course.id

        for role in [CourseInstructorRole, CourseStaffRole]:
            role(self.source_course_key).add_users(self.user)

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        ModuleStoreTestCase.tearDown(self)

    def test_rerun(self):
        """
        Just testing the functionality the view handler adds over the tasks tested in test_clone_course
        """
        add_organization({
            'name': 'Test Organization',
            'short_name': self.source_course_key.org,
            'description': 'Testing Organization Description',
        })
        response = self.client.ajax_post(self.course_create_rerun_url, {
            'source_course_key': six.text_type(self.source_course_key),
            'org': self.source_course_key.org, 'course': self.source_course_key.course, 'run': 'copy',
            'display_name': 'not the same old name',
        })
        self.assertEqual(response.status_code, 200)
        data = parse_json(response)
        dest_course_key = CourseKey.from_string(data['destination_course_key'])

        self.assertEqual(dest_course_key.run, 'copy')
        source_course = self.store.get_course(self.source_course_key)
        dest_course = self.store.get_course(dest_course_key)
        self.assertEqual(dest_course.start, CourseFields.start.default)
        self.assertEqual(dest_course.end, source_course.end)
        self.assertEqual(dest_course.enrollment_start, None)
        self.assertEqual(dest_course.enrollment_end, None)
        course_orgs = get_course_organizations(dest_course_key)
        self.assertEqual(len(course_orgs), 1)
        self.assertEqual(course_orgs[0]['short_name'], self.source_course_key.org)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_newly_created_course_has_web_certs_enabled(self, store):
        """
        Tests newly created course has web certs enabled by default.
        """
        with modulestore().default_store(store):
            response = self.client.ajax_post(self.course_create_rerun_url, {
                'org': 'orgX',
                'number': 'CS101',
                'display_name': 'Course with web certs enabled',
                'run': '2015_T2'
            })
            self.assertEqual(response.status_code, 200)
            data = parse_json(response)
            new_course_key = CourseKey.from_string(data['course_key'])
            course = self.store.get_course(new_course_key)
            self.assertTrue(course.cert_html_view_enabled)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_creation_for_unknown_organization_relaxed(self, store):
        """
        Tests that when ORGANIZATIONS_AUTOCREATE is True,
        creating a course-run with an unknown org slug will create an organization
        and organization-course linkage in the system.
        """
        with self.assertRaises(InvalidOrganizationException):
            get_organization_by_short_name("orgX")
        with modulestore().default_store(store):
            response = self.client.ajax_post(self.course_create_rerun_url, {
                'org': 'orgX',
                'number': 'CS101',
                'display_name': 'Course with web certs enabled',
                'run': '2015_T2'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(get_organization_by_short_name("orgX"))
            data = parse_json(response)
            new_course_key = CourseKey.from_string(data['course_key'])
            course_orgs = get_course_organizations(new_course_key)
            self.assertEqual(len(course_orgs), 1)
            self.assertEqual(course_orgs[0]['short_name'], 'orgX')

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    @override_settings(ORGANIZATIONS_AUTOCREATE=False)
    def test_course_creation_for_unknown_organization_strict(self, store):
        """
        Tests that when ORGANIZATIONS_AUTOCREATE is False,
        creating a course-run with an unknown org slug will raise a validation error.
        """
        with modulestore().default_store(store):
            response = self.client.ajax_post(self.course_create_rerun_url, {
                'org': 'orgX',
                'number': 'CS101',
                'display_name': 'Course with web certs enabled',
                'run': '2015_T2'
            })
            self.assertEqual(response.status_code, 400)
            with self.assertRaises(InvalidOrganizationException):
                get_organization_by_short_name("orgX")
            data = parse_json(response)
            self.assertIn(u'Organization you selected does not exist in the system', data['error'])

    @ddt.data(True, False)
    def test_course_creation_for_known_organization(self, organizations_autocreate):
        """
        Tests course creation workflow when course organization exist in system.
        """
        add_organization({
            'name': 'Test Organization',
            'short_name': 'orgX',
            'description': 'Testing Organization Description',
        })
        with override_settings(ORGANIZATIONS_AUTOCREATE=organizations_autocreate):
            response = self.client.ajax_post(self.course_create_rerun_url, {
                'org': 'orgX',
                'number': 'CS101',
                'display_name': 'Course with web certs enabled',
                'run': '2015_T2'
            })
            self.assertEqual(response.status_code, 200)
            data = parse_json(response)
            new_course_key = CourseKey.from_string(data['course_key'])
            course_orgs = get_course_organizations(new_course_key)
            self.assertEqual(len(course_orgs), 1)
            self.assertEqual(course_orgs[0]['short_name'], 'orgX')
