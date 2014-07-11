""" Unit tests for utility methods in views.py. """
from django.conf import settings
from xmodule.modulestore.django import modulestore
from contentstore.utils import reverse_course_url
from contentstore.views.utility import expand_utility_action_url
from xmodule.modulestore.tests.factories import CourseFactory

import json
import mock
from .utils import CourseTestCase


class UtilitiesTestCase(CourseTestCase):
    """ Test for utility get and put methods. """
    def setUp(self):
        """ Creates the test course. """
        super(UtilitiesTestCase, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Utilities Course')
        self.utilities_url = reverse_course_url('utility_handler', self.course.id)

    def get_persisted_utilities(self):
        """ Returns the utilities. """
        return settings.COURSE_UTILITIES

    def compare_utilities(self, persisted, request):
        """
        Handles url expansion as possible difference and descends into guts
        """
        self.assertEqual(persisted['short_description'], request['short_description'])
        expanded_utility = expand_utility_action_url(self.course, persisted)
        for pers, req in zip(expanded_utility['items'], request['items']):
            self.assertEqual(pers['short_description'], req['short_description'])
            self.assertEqual(pers['long_description'], req['long_description'])
            self.assertEqual(pers['action_url'], req['action_url'])
            self.assertEqual(pers['action_text'], req['action_text'])
            self.assertEqual(pers['action_external'], req['action_external'])

    def test_get_utilities(self):
        """ Tests the get utilities method and URL expansion. """
        response = self.client.get(self.utilities_url)
        self.assertContains(response, "Bulk Operations")
        # Verify expansion of action URL happened.
        self.assertContains(response, '/utility/captions/slashes:mitX+333+Utilities_Course')
        # Verify persisted utility does NOT have expanded URL.
        utility_0 = self.get_persisted_utilities()[0]
        self.assertEqual('utility_captions_handler', get_action_url(utility_0, 0))
        payload = response.content

        # Now delete the utilities from the course and verify they get repopulated (for courses
        # created before utilities were introduced).
        with mock.patch('django.conf.settings.COURSE_UTILITIES', []):
            modulestore().update_item(self.course, self.user.id)
            self.assertEqual(self.get_persisted_utilities(), [])

    def test_get_utilities_html(self):
        """ Tests getting the HTML template for the utilities page). """
        response = self.client.get(self.utilities_url, HTTP_ACCEPT='text/html')
        self.assertContains(response, "What are course utilities?")
        # The HTML generated will define the handler URL (for use by the Backbone model).
        self.assertContains(response, self.utilities_url)

    def test_update_utilities_no_index(self):
        """ No utility index, should return all of them. """
        returned_utilities = json.loads(self.client.get(self.utilities_url).content)
        # Verify that persisted utilities do not have expanded action URLs.
        # compare_utilities will verify that returned_utilities DO have expanded action URLs.
        pers = self.get_persisted_utilities()
        self.assertEqual('utility_captions_handler', get_first_item(pers[0]).get('action_url'))
        for pay, resp in zip(pers, returned_utilities):
            self.compare_utilities(pay, resp)

    def test_utilities_post_unsupported(self):
        """ Post operation is not supported. """
        update_url = reverse_course_url('utility_handler', self.course.id)
        response = self.client.post(update_url)
        self.assertEqual(response.status_code, 405)

    def test_utilities_put_unsupported(self):
        """ Put operation is not supported. """
        update_url = reverse_course_url('utility_handler', self.course.id)
        response = self.client.put(update_url)
        self.assertEqual(response.status_code, 405)

    def test_utilities_delete_unsupported(self):
        """ Delete operation is not supported. """
        update_url = reverse_course_url('utility_handler', self.course.id)
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, 405)

    def test_expand_utility_action_url(self):
        """
        Tests the method to expand utility action url.
        """

        def test_expansion(utility, index, stored, expanded):
            """
            Tests that the expected expanded value is returned for the item at the given index.

            Also verifies that the original utility is not modified.
            """
            self.assertEqual(get_action_url(utility, index), stored)
            expanded_utility = expand_utility_action_url(self.course, utility)
            self.assertEqual(get_action_url(expanded_utility, index), expanded)
            # Verify no side effect in the original list.
            self.assertEqual(get_action_url(utility, index), stored)

        test_expansion(settings.COURSE_UTILITIES[0], 0, 'utility_captions_handler', '/utility/captions/slashes:mitX+333+Utilities_Course')


def get_first_item(utility):
    """ Returns the first item from the utility. """
    return utility['items'][0]


def get_action_url(utility, index):
    """
    Returns the action_url for the item at the specified index in the given utility.
    """
    return utility['items'][index]['action_url']
