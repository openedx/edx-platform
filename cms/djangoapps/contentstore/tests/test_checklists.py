""" Unit tests for checklist methods in views.py. """
from contentstore.utils import get_modulestore, get_url_reverse
from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.tests.factories import CourseFactory
from django.core.urlresolvers import reverse
import json


class ChecklistTestCase(CourseTestCase):
    """ Test for checklist get and put methods. """
    def setUp(self):
        """ Creates the test course. """
        super(ChecklistTestCase, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Checklists Course')

    def get_persisted_checklists(self):
        """ Returns the checklists as persisted in the modulestore. """
        modulestore = get_modulestore(self.course.location)
        return modulestore.get_item(self.course.location).checklists

    def compare_checklists(self, persisted, request):
        """
        Handles url expansion as possible difference and descends into guts
        :param persisted:
        :param request:
        """
        self.assertEqual(persisted['short_description'], request['short_description'])
        compare_urls = (persisted.get('action_urls_expanded') == request.get('action_urls_expanded'))
        for pers, req in zip(persisted['items'], request['items']):
            self.assertEqual(pers['short_description'], req['short_description'])
        self.assertEqual(pers['long_description'], req['long_description'])
        self.assertEqual(pers['is_checked'], req['is_checked'])
        if compare_urls:
            self.assertEqual(pers['action_url'], req['action_url'])
        self.assertEqual(pers['action_text'], req['action_text'])
        self.assertEqual(pers['action_external'], req['action_external'])

    def test_get_checklists(self):
        """ Tests the get checklists method. """
        checklists_url = get_url_reverse('Checklists', self.course)
        response = self.client.get(checklists_url)
        self.assertContains(response, "Getting Started With Studio")
        payload = response.content

        # Now delete the checklists from the course and verify they get repopulated (for courses
        # created before checklists were introduced).
        self.course.checklists = None
        modulestore = get_modulestore(self.course.location)
        modulestore.update_metadata(self.course.location, own_metadata(self.course))
        self.assertEqual(self.get_persisted_checklists(), None)
        response = self.client.get(checklists_url)
        self.assertEqual(payload, response.content)

    def test_update_checklists_no_index(self):
        """ No checklist index, should return all of them. """
        update_url = reverse('checklists_updates', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name})

        returned_checklists = json.loads(self.client.get(update_url).content)
        for pay, resp in zip(self.get_persisted_checklists(), returned_checklists):
            self.compare_checklists(pay, resp)

    def test_update_checklists_index_ignored_on_get(self):
        """ Checklist index ignored on get. """
        update_url = reverse('checklists_updates', kwargs={'org': self.course.location.org,
                                                           'course': self.course.location.course,
                                                           'name': self.course.location.name,
                                                           'checklist_index': 1})

        returned_checklists = json.loads(self.client.get(update_url).content)
        for pay, resp in zip(self.get_persisted_checklists(), returned_checklists):
            self.compare_checklists(pay, resp)

    def test_update_checklists_post_no_index(self):
        """ No checklist index, will error on post. """
        update_url = reverse('checklists_updates', kwargs={'org': self.course.location.org,
                                                           'course': self.course.location.course,
                                                           'name': self.course.location.name})
        response = self.client.post(update_url)
        self.assertContains(response, 'Could not save checklist', status_code=400)

    def test_update_checklists_index_out_of_range(self):
        """ Checklist index out of range, will error on post. """
        update_url = reverse('checklists_updates', kwargs={'org': self.course.location.org,
                                                           'course': self.course.location.course,
                                                           'name': self.course.location.name,
                                                           'checklist_index': 100})
        response = self.client.post(update_url)
        self.assertContains(response, 'Could not save checklist', status_code=400)

    def test_update_checklists_index(self):
        """ Check that an update of a particular checklist works. """
        update_url = reverse('checklists_updates', kwargs={'org': self.course.location.org,
                                                           'course': self.course.location.course,
                                                           'name': self.course.location.name,
                                                           'checklist_index': 2})

        def get_first_item(checklist):
            return checklist['items'][0]

        payload = self.course.checklists[2]
        self.assertFalse(get_first_item(payload).get('is_checked'))
        get_first_item(payload)['is_checked'] = True

        returned_checklist = json.loads(self.client.post(update_url, json.dumps(payload), "application/json").content)
        self.assertTrue(get_first_item(returned_checklist).get('is_checked'))
        pers = self.get_persisted_checklists()
        self.compare_checklists(pers[2], returned_checklist)

    def test_update_checklists_delete_unsupported(self):
        """ Delete operation is not supported. """
        update_url = reverse('checklists_updates', kwargs={'org': self.course.location.org,
                                                           'course': self.course.location.course,
                                                           'name': self.course.location.name,
                                                           'checklist_index': 100})
        response = self.client.delete(update_url)
        self.assertContains(response, 'Unsupported request', status_code=400)
