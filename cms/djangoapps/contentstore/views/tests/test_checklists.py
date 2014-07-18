""" Unit tests for checklist methods in views.py. """
from contentstore.utils import reverse_course_url
from contentstore.views.checklist import expand_checklist_action_url
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore

import json
from contentstore.tests.utils import CourseTestCase


class ChecklistTestCase(CourseTestCase):
    """ Test for checklist get and put methods. """
    def setUp(self):
        """ Creates the test course. """
        super(ChecklistTestCase, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Checklists Course')
        self.checklists_url = self.get_url()

    def get_url(self, checklist_index=None):
        url_args = {'checklist_index': checklist_index} if checklist_index else None
        return reverse_course_url('checklists_handler', self.course.id, kwargs=url_args)

    def get_persisted_checklists(self):
        """ Returns the checklists as persisted in the modulestore. """
        return modulestore().get_item(self.course.location).checklists

    def compare_checklists(self, persisted, request):
        """
        Handles url expansion as possible difference and descends into guts
        """
        self.assertEqual(persisted['short_description'], request['short_description'])
        expanded_checklist = expand_checklist_action_url(self.course, persisted)
        for pers, req in zip(expanded_checklist['items'], request['items']):
            self.assertEqual(pers['short_description'], req['short_description'])
            self.assertEqual(pers['long_description'], req['long_description'])
            self.assertEqual(pers['is_checked'], req['is_checked'])
            self.assertEqual(pers['action_url'], req['action_url'])
            self.assertEqual(pers['action_text'], req['action_text'])
            self.assertEqual(pers['action_external'], req['action_external'])

    def test_get_checklists(self):
        """ Tests the get checklists method and URL expansion. """
        response = self.client.get(self.checklists_url)
        self.assertContains(response, "Getting Started With Studio")
        # Verify expansion of action URL happened.
        self.assertContains(response, 'course_team/mitX/333/Checklists_Course')
        # Verify persisted checklist does NOT have expanded URL.
        checklist_0 = self.get_persisted_checklists()[0]
        self.assertEqual('ManageUsers', get_action_url(checklist_0, 0))
        payload = response.content

        # Now delete the checklists from the course and verify they get repopulated (for courses
        # created before checklists were introduced).
        self.course.checklists = None
        # Save the changed `checklists` to the underlying KeyValueStore before updating the modulestore
        self.course.save()
        modulestore().update_item(self.course, self.user.id)
        self.assertEqual(self.get_persisted_checklists(), None)
        response = self.client.get(self.checklists_url)
        self.assertEqual(payload, response.content)

    def test_get_checklists_html(self):
        """ Tests getting the HTML template for the checklists page). """
        response = self.client.get(self.checklists_url, HTTP_ACCEPT='text/html')
        self.assertContains(response, "Getting Started With Studio")
        # The HTML generated will define the handler URL (for use by the Backbone model).
        self.assertContains(response, self.checklists_url)

    def test_update_checklists_no_index(self):
        """ No checklist index, should return all of them. """
        returned_checklists = json.loads(self.client.get(self.checklists_url).content)
        # Verify that persisted checklists do not have expanded action URLs.
        # compare_checklists will verify that returned_checklists DO have expanded action URLs.
        pers = self.get_persisted_checklists()
        self.assertEqual('CourseOutline', get_first_item(pers[1]).get('action_url'))
        for pay, resp in zip(pers, returned_checklists):
            self.compare_checklists(pay, resp)

    def test_update_checklists_index_ignored_on_get(self):
        """ Checklist index ignored on get. """
        update_url = self.get_url(1)

        returned_checklists = json.loads(self.client.get(update_url).content)
        for pay, resp in zip(self.get_persisted_checklists(), returned_checklists):
            self.compare_checklists(pay, resp)

    def test_update_checklists_post_no_index(self):
        """ No checklist index, will error on post. """
        response = self.client.post(self.checklists_url)
        self.assertContains(response, 'Could not save checklist', status_code=400)

    def test_update_checklists_index_out_of_range(self):
        """ Checklist index out of range, will error on post. """
        update_url = self.get_url(100)

        response = self.client.post(update_url)
        self.assertContains(response, 'Could not save checklist', status_code=400)

    def test_update_checklists_index(self):
        """ Check that an update of a particular checklist works. """
        update_url = self.get_url(1)

        payload = self.course.checklists[1]
        self.assertFalse(get_first_item(payload).get('is_checked'))
        self.assertEqual('CourseOutline', get_first_item(payload).get('action_url'))
        get_first_item(payload)['is_checked'] = True

        returned_checklist = json.loads(self.client.ajax_post(update_url, payload).content)
        self.assertTrue(get_first_item(returned_checklist).get('is_checked'))
        persisted_checklist = self.get_persisted_checklists()[1]
        # Verify that persisted checklist does not have expanded action URLs.
        # compare_checklists will verify that returned_checklist DOES have expanded action URLs.
        self.assertEqual('CourseOutline', get_first_item(persisted_checklist).get('action_url'))
        self.compare_checklists(persisted_checklist, returned_checklist)

    def test_update_checklists_delete_unsupported(self):
        """ Delete operation is not supported. """
        update_url = self.get_url(100)
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, 405)

    def test_expand_checklist_action_url(self):
        """
        Tests the method to expand checklist action url.
        """

        def test_expansion(checklist, index, stored, expanded):
            """
            Tests that the expected expanded value is returned for the item at the given index.

            Also verifies that the original checklist is not modified.
            """
            self.assertEqual(get_action_url(checklist, index), stored)
            expanded_checklist = expand_checklist_action_url(self.course, checklist)
            self.assertEqual(get_action_url(expanded_checklist, index), expanded)
            # Verify no side effect in the original list.
            self.assertEqual(get_action_url(checklist, index), stored)

        test_expansion(self.course.checklists[0], 0, 'ManageUsers', '/course_team/mitX/333/Checklists_Course/')
        test_expansion(self.course.checklists[1], 1, 'CourseOutline', '/course/mitX/333/Checklists_Course')
        test_expansion(self.course.checklists[2], 0, 'http://help.edge.edx.org/', 'http://help.edge.edx.org/')


def get_first_item(checklist):
    """ Returns the first item from the checklist. """
    return checklist['items'][0]


def get_action_url(checklist, index):
    """
    Returns the action_url for the item at the specified index in the given checklist.
    """
    return checklist['items'][index]['action_url']
