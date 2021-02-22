"""
Tests for course welcome messages.
"""

import ddt
from django.urls import reverse

from openedx.features.course_experience.tests import BaseCourseUpdatesTestCase


def welcome_message_url(course):
    """
    Returns the URL for the welcome message view.
    """
    return reverse(
        'openedx.course_experience.welcome_message_fragment_view',
        kwargs={
            'course_id': str(course.id),
        }
    )


def latest_update_url(course):
    """
    Returns the URL for the latest update view.
    """
    return reverse(
        'openedx.course_experience.latest_update_fragment_view',
        kwargs={
            'course_id': str(course.id),
        }
    )


def dismiss_message_url(course):
    """
    Returns the URL for the dismiss message endpoint.
    """
    return reverse(
        'openedx.course_experience.dismiss_welcome_message',
        kwargs={
            'course_id': str(course.id),
        }
    )


@ddt.ddt
class TestWelcomeMessageView(BaseCourseUpdatesTestCase):
    """
    Tests for the course welcome message fragment view.

    Also tests the LatestUpdate view because the functionality is similar.
    """
    @ddt.data(welcome_message_url, latest_update_url)
    def test_message_display(self, url_generator):
        self.create_course_update('First Update', date='January 1, 2000')
        self.create_course_update('Second Update', date='January 1, 2017')
        self.create_course_update('Retroactive Update', date='January 1, 2010')
        response = self.client.get(url_generator(self.course))
        assert response.status_code == 200
        self.assertContains(response, 'Second Update')
        self.assertContains(response, 'Dismiss')

    @ddt.data(welcome_message_url, latest_update_url)
    def test_empty_message(self, url_generator):
        response = self.client.get(url_generator(self.course))
        assert response.status_code == 204

    def test_dismiss_welcome_message(self):
        # Latest update is dimssed in JS and has no server/backend component.
        self.create_course_update('First Update')

        response = self.client.get(welcome_message_url(self.course))
        assert response.status_code == 200
        self.assertContains(response, 'First Update')

        self.client.post(dismiss_message_url(self.course))
        response = self.client.get(welcome_message_url(self.course))
        assert 'First Update' not in response
        assert response.status_code == 204
