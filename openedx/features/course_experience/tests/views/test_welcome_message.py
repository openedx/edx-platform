"""
Tests for course welcome messages.
"""


import ddt
import six
from django.urls import reverse

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .test_course_updates import create_course_update, remove_course_updates

TEST_PASSWORD = 'test'
TEST_WELCOME_MESSAGE = '<h2>Welcome!</h2>'


def welcome_message_url(course):
    """
    Returns the URL for the welcome message view.
    """
    return reverse(
        'openedx.course_experience.welcome_message_fragment_view',
        kwargs={
            'course_id': six.text_type(course.id),
        }
    )


def latest_update_url(course):
    """
    Returns the URL for the latest update view.
    """
    return reverse(
        'openedx.course_experience.latest_update_fragment_view',
        kwargs={
            'course_id': six.text_type(course.id),
        }
    )


def dismiss_message_url(course):
    """
    Returns the URL for the dismiss message endpoint.
    """
    return reverse(
        'openedx.course_experience.dismiss_welcome_message',
        kwargs={
            'course_id': six.text_type(course.id),
        }
    )


@ddt.ddt
class TestWelcomeMessageView(ModuleStoreTestCase):
    """
    Tests for the course welcome message fragment view.

    Also tests the LatestUpdate view because the functionality is similar.
    """
    def setUp(self):
        """Set up the simplest course possible, then set up and enroll our fake user in the course."""
        super(TestWelcomeMessageView, self).setUp()
        with self.store.default_store(ModuleStoreEnum.Type.split):
            self.course = CourseFactory.create()
            with self.store.bulk_operations(self.course.id):
                # Create a basic course structure
                chapter = ItemFactory.create(category='chapter', parent_location=self.course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                ItemFactory.create(category='vertical', parent_location=section.location)
        self.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(self.user, self.course.id)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def tearDown(self):
        remove_course_updates(self.user, self.course)
        super(TestWelcomeMessageView, self).tearDown()

    @ddt.data(welcome_message_url, latest_update_url)
    def test_message_display(self, url_generator):
        create_course_update(self.course, self.user, 'First Update', date='January 1, 2000')
        create_course_update(self.course, self.user, 'Second Update', date='January 1, 2017')
        create_course_update(self.course, self.user, 'Retroactive Update', date='January 1, 2010')
        response = self.client.get(url_generator(self.course))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Update')
        self.assertContains(response, 'Dismiss')

    @ddt.data(welcome_message_url, latest_update_url)
    def test_replace_urls(self, url_generator):
        img_url = 'img.png'
        create_course_update(self.course, self.user, u"<img src='/static/{url}'>".format(url=img_url))
        response = self.client.get(url_generator(self.course))
        self.assertContains(response, "/asset-v1:{org}+{course}+{run}+type@asset+block/{url}".format(
            org=self.course.id.org,
            course=self.course.id.course,
            run=self.course.id.run,
            url=img_url,
        ))

    @ddt.data(welcome_message_url, latest_update_url)
    def test_empty_message(self, url_generator):
        response = self.client.get(url_generator(self.course))
        self.assertEqual(response.status_code, 204)

    def test_dismiss_welcome_message(self):
        # Latest update is dimssed in JS and has no server/backend component.
        create_course_update(self.course, self.user, 'First Update', date='January 1, 2017')

        response = self.client.get(welcome_message_url(self.course))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Update')

        self.client.post(dismiss_message_url(self.course))
        response = self.client.get(welcome_message_url(self.course))
        self.assertNotIn('First Update', response)
        self.assertEqual(response.status_code, 204)
