"""
Tests for the maintenance app views.
"""
import ddt
import json

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


from contentstore.management.commands.utils import get_course_versions
from student.tests.factories import AdminFactory, UserFactory

from .views import COURSE_KEY_ERROR_MESSAGES, MAINTENANCE_VIEWS


# This list contains URLs of all maintenance app views.
MAINTENANCE_URLS = [reverse(view['url']) for view in MAINTENANCE_VIEWS.values()]


class TestMaintenanceIndex(ModuleStoreTestCase):
    """
    Tests for maintenance index view.
    """

    def setUp(self):
        super(TestMaintenanceIndex, self).setUp()
        self.user = AdminFactory()
        login_success = self.client.login(username=self.user.username, password='test')
        self.assertTrue(login_success)
        self.view_url = reverse('maintenance:maintenance_index')

    def test_maintenance_index(self):
        """
        Test that maintenance index view lists all the maintenance app views.
        """
        response = self.client.get(self.view_url)
        self.assertContains(response, 'Maintenance', status_code=200)

        # Check that all the expected links appear on the index page.
        for url in MAINTENANCE_URLS:
            self.assertContains(response, url, status_code=200)


@ddt.ddt
class MaintenanceViewTestCase(ModuleStoreTestCase):
    """
    Base class for maintenance view tests.
    """
    view_url = ''

    def setUp(self):
        super(MaintenanceViewTestCase, self).setUp()
        self.user = AdminFactory()
        login_success = self.client.login(username=self.user.username, password='test')
        self.assertTrue(login_success)

    def verify_error_message(self, data, error_message):
        """
        Verify the response contains error message.
        """
        response = self.client.post(self.view_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, error_message, status_code=200)

    def tearDown(self):
        """
        Reverse the setup.
        """
        self.client.logout()
        super(MaintenanceViewTestCase, self).tearDown()


@ddt.ddt
class MaintenanceViewAccessTests(MaintenanceViewTestCase):
    """
    Tests for access control of maintenance views.
    """
    @ddt.data(MAINTENANCE_URLS)
    @ddt.unpack
    def test_require_login(self, url):
        """
        Test that maintenance app requires user login.
        """
        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = '{login_url}?next={original_url}'.format(
            login_url=reverse('login'),
            original_url=url,
        )

        self.assertRedirects(response, redirect_url)

    @ddt.data(MAINTENANCE_URLS)
    @ddt.unpack
    def test_global_staff_access(self, url):
        """
        Test that all maintenance app views are accessible to global staff user.
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @ddt.data(MAINTENANCE_URLS)
    @ddt.unpack
    def test_non_global_staff_access(self, url):
        """
        Test that all maintenance app views are not accessible to non-global-staff user.
        """
        user = UserFactory(username='test', email='test@example.com', password='test')
        login_success = self.client.login(username=user.username, password='test')
        self.assertTrue(login_success)

        response = self.client.get(url)
        self.assertContains(
            response,
            u'Must be {platform_name} staff to perform this action.'.format(platform_name=settings.PLATFORM_NAME),
            status_code=403
        )


@ddt.ddt
class TestForcePublish(MaintenanceViewTestCase):
    """
    Tests for the force publish view.
    """

    def setUp(self):
        super(TestForcePublish, self).setUp()
        self.view_url = reverse('maintenance:force_publish_course')

    def setup_test_course(self):
        """
        Creates the course and add some changes to it.

        Returns:
            course: a course object
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        # Add some changes to course
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        self.store.create_child(
            self.user.id,  # pylint: disable=no-member
            chapter.location,
            'html',
            block_id='html_component'
        )
        # verify that course has changes.
        self.assertTrue(self.store.has_changes(self.store.get_item(course.location)))
        return course

    @ddt.data(
        ('', COURSE_KEY_ERROR_MESSAGES['empty_course_key']),
        ('edx', COURSE_KEY_ERROR_MESSAGES['invalid_course_key']),
        ('course-v1:e+d+X', COURSE_KEY_ERROR_MESSAGES['course_key_not_found']),
    )
    @ddt.unpack
    def test_invalid_course_key_messages(self, course_key, error_message):
        """
        Test all error messages for invalid course keys.
        """
        # validate that course key contains error message
        self.verify_error_message(
            data={'course-id': course_key},
            error_message=error_message
        )

    def test_mongo_course(self):
        """
        Test that we get a error message on old mongo courses.
        """
        # validate non split error message
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.mongo)
        self.verify_error_message(
            data={'course-id': unicode(course.id)},
            error_message='Force publishing course is not supported with old mongo courses.'
        )

    def test_mongo_course_with_split_course_key(self):
        """
        Test that we get an error message `course_key_not_found` for a provided split course key
        if we already have an old mongo course.
        """
        # validate non split error message
        course = CourseFactory.create(org='e', number='d', run='X', default_store=ModuleStoreEnum.Type.mongo)
        self.verify_error_message(
            data={'course-id': unicode(course.id)},
            error_message='Force publishing course is not supported with old mongo courses.'
        )
        # Now search for the course key in split version.
        self.verify_error_message(
            data={'course-id': 'course-v1:e+d+X'},
            error_message=COURSE_KEY_ERROR_MESSAGES['course_key_not_found']
        )

    def test_already_published(self):
        """
        Test that when a course is forcefully publish, we get a 'course is already published' message.
        """
        course = self.setup_test_course()

        # publish the course
        source_store = modulestore()._get_modulestore_for_courselike(course.id)  # pylint: disable=protected-access
        source_store.force_publish_course(course.id, self.user.id, commit=True)  # pylint: disable=no-member

        # now course is published, we should get `already published course` error.
        self.verify_error_message(
            data={'course-id': unicode(course.id)},
            error_message='Course is already in published state.'
        )

    def verify_versions_are_different(self, course):
        """
        Verify draft and published versions point to different locations.

        Arguments:
            course (object): a course object.
        """
        # get draft and publish branch versions
        versions = get_course_versions(unicode(course.id))

        # verify that draft and publish point to different versions
        self.assertNotEqual(versions['draft-branch'], versions['published-branch'])

    def get_force_publish_course_response(self, course):
        """
        Get force publish the course response.

        Arguments:
            course (object): a course object.

        Returns:
            response : response from force publish post view.
        """
        # Verify versions point to different locations initially
        self.verify_versions_are_different(course)

        # force publish course view
        data = {
            'course-id': unicode(course.id)
        }
        response = self.client.post(self.view_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_data = json.loads(response.content)
        return response_data

    def test_force_publish_dry_run(self):
        """
        Test that dry run does not publishes the course but shows possible outcome if force published is executed.
        """
        course = self.setup_test_course()
        response = self.get_force_publish_course_response(course)

        self.assertIn('current_versions', response)

        # verify that course still has changes as we just dry ran force publish course.
        self.assertTrue(self.store.has_changes(self.store.get_item(course.location)))

        # verify that both branch versions are still different
        self.verify_versions_are_different(course)
