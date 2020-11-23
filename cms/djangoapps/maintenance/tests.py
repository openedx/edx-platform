"""
Tests for the maintenance app views.
"""


import json

import ddt
import six
from django.conf import settings
from django.urls import reverse

from cms.djangoapps.contentstore.management.commands.utils import get_course_versions
from openedx.features.announcements.models import Announcement
from common.djangoapps.student.tests.factories import AdminFactory, UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

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
    @ddt.data(*MAINTENANCE_URLS)
    def test_require_login(self, url):
        """
        Test that maintenance app requires user login.
        """
        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = '{login_url}?next={original_url}'.format(
            login_url=settings.LOGIN_URL,
            original_url=url,
        )

        # Studio login redirects to LMS login
        self.assertRedirects(response, redirect_url, target_status_code=302)

    @ddt.data(*MAINTENANCE_URLS)
    def test_global_staff_access(self, url):
        """
        Test that all maintenance app views are accessible to global staff user.
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @ddt.data(*MAINTENANCE_URLS)
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
            self.user.id,
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
            data={'course-id': six.text_type(course.id)},
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
            data={'course-id': six.text_type(course.id)},
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
        source_store.force_publish_course(course.id, self.user.id, commit=True)

        # now course is published, we should get `already published course` error.
        self.verify_error_message(
            data={'course-id': six.text_type(course.id)},
            error_message='Course is already in published state.'
        )

    def verify_versions_are_different(self, course):
        """
        Verify draft and published versions point to different locations.

        Arguments:
            course (object): a course object.
        """
        # get draft and publish branch versions
        versions = get_course_versions(six.text_type(course.id))

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
            'course-id': six.text_type(course.id)
        }
        response = self.client.post(self.view_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_data = json.loads(response.content.decode('utf-8'))
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


@ddt.ddt
class TestAnnouncementsViews(MaintenanceViewTestCase):
    """
    Tests for the announcements edit view.
    """

    def setUp(self):
        super(TestAnnouncementsViews, self).setUp()
        self.admin = AdminFactory.create(
            email='staff@edx.org',
            username='admin',
            password='pass'
        )
        self.client.login(username=self.admin.username, password='pass')
        self.non_staff_user = UserFactory.create(
            email='test@edx.org',
            username='test',
            password='pass'
        )

    def test_index(self):
        """
        Test create announcement view
        """
        url = reverse("maintenance:announcement_index")
        response = self.client.get(url)
        self.assertContains(response, '<div class="announcement-container">')

    def test_create(self):
        """
        Test create announcement view
        """
        url = reverse("maintenance:announcement_create")
        self.client.post(url, {"content": "Test Create Announcement", "active": True})
        result = Announcement.objects.filter(content="Test Create Announcement").exists()
        self.assertTrue(result)

    def test_edit(self):
        """
        Test edit announcement view
        """
        announcement = Announcement.objects.create(content="test")
        announcement.save()
        url = reverse("maintenance:announcement_edit", kwargs={"pk": announcement.pk})
        response = self.client.get(url)
        self.assertContains(response, '<div class="wrapper-form announcement-container">')
        self.client.post(url, {"content": "Test Edit Announcement", "active": True})
        announcement = Announcement.objects.get(pk=announcement.pk)
        self.assertEqual(announcement.content, "Test Edit Announcement")

    def test_delete(self):
        """
        Test delete announcement view
        """
        announcement = Announcement.objects.create(content="Test Delete")
        announcement.save()
        url = reverse("maintenance:announcement_delete", kwargs={"pk": announcement.pk})
        self.client.post(url)
        result = Announcement.objects.filter(content="Test Edit Announcement").exists()
        self.assertFalse(result)

    def _test_403(self, viewname, kwargs=None):
        url = reverse("maintenance:%s" % viewname, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authorization(self):
        self.client.login(username=self.non_staff_user, password='pass')
        announcement = Announcement.objects.create(content="Test Delete")
        announcement.save()

        self._test_403("announcement_index")
        self._test_403("announcement_create")
        self._test_403("announcement_edit", {"pk": announcement.pk})
        self._test_403("announcement_delete", {"pk": announcement.pk})
