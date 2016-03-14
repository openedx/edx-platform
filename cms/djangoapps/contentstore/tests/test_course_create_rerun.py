"""
Test view handler for rerun (and eventually create)
"""
import ddt
from mock import patch

from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from contentstore.tests.utils import AjaxEnabledTestClient, parse_json
from datetime import datetime
from xmodule.course_module import CourseFields
from util.organizations_helpers import (
    add_organization,
    get_course_organizations,
)


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
        source_course = CourseFactory.create(
            org='origin',
            number='the_beginning',
            run='first',
            display_name='the one and only',
            start=datetime.utcnow()
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
        response = self.client.ajax_post(self.course_create_rerun_url, {
            'source_course_key': unicode(self.source_course_key),
            'org': self.source_course_key.org, 'course': self.source_course_key.course, 'run': 'copy',
            'display_name': 'not the same old name',
        })
        self.assertEqual(response.status_code, 200)
        data = parse_json(response)
        dest_course_key = CourseKey.from_string(data['destination_course_key'])

        self.assertEqual(dest_course_key.run, 'copy')
        dest_course = self.store.get_course(dest_course_key)
        self.assertEqual(dest_course.start, CourseFields.start.default)

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

    @patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': False})
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_creation_without_org_app_enabled(self, store):
        """
        Tests course creation workflow should not create course to org
        link if organizations_app is not enabled.
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
            course_orgs = get_course_organizations(new_course_key)
            self.assertEqual(course_orgs, [])

    @patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': True})
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_creation_with_org_not_in_system(self, store):
        """
        Tests course creation workflow when course organization does not exist
        in system.
        """
        with modulestore().default_store(store):
            response = self.client.ajax_post(self.course_create_rerun_url, {
                'org': 'orgX',
                'number': 'CS101',
                'display_name': 'Course with web certs enabled',
                'run': '2015_T2'
            })
            self.assertEqual(response.status_code, 400)
            data = parse_json(response)
            self.assertIn(u'Organization you selected does not exist in the system', data['error'])

    @patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': True})
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_creation_with_org_in_system(self, store):
        """
        Tests course creation workflow when course organization exist in system.
        """
        add_organization({
            'name': 'Test Organization',
            'short_name': 'orgX',
            'description': 'Testing Organization Description',
        })
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
            course_orgs = get_course_organizations(new_course_key)
            self.assertEqual(len(course_orgs), 1)
            self.assertEqual(course_orgs[0]['short_name'], 'orgX')
