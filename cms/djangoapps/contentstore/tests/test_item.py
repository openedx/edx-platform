"""Tests for items views."""

import json
import datetime
from pytz import UTC

from contentstore.tests.utils import CourseTestCase
from xmodule.capa_module import CapaDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator


class ItemTest(CourseTestCase):
    """ Base test class for create, save, and delete """
    def setUp(self):
        super(ItemTest, self).setUp()

        self.unicode_locator = unicode(loc_mapper().translate_location(
            self.course.location.course_id, self.course.location, False, True
        ))

    def get_old_id(self, locator):
        """
        Converts new locator to old id format (forcing to non-draft).
        """
        return loc_mapper().translate_locator_to_location(BlockUsageLocator(locator)).replace(revision=None)

    def get_item_from_modulestore(self, locator, draft=False):
        """
        Get the item referenced by the locator from the modulestore
        """
        store = modulestore('draft') if draft else modulestore()
        return store.get_item(self.get_old_id(locator))

    def response_locator(self, response):
        """
        Get the locator (unicode representation) from the response payload
        :param response:
        """
        parsed = json.loads(response.content)
        return parsed['locator']

    def create_xblock(self, parent_locator=None, display_name=None, category=None, boilerplate=None):
        data = {
            'parent_locator': self.unicode_locator if parent_locator is None else parent_locator,
            'category': category
        }
        if display_name is not None:
            data['display_name'] = display_name
        if boilerplate is not None:
            data['boilerplate'] = boilerplate
        return self.client.ajax_post('/xblock', json.dumps(data))


class DeleteItem(ItemTest):
    """Tests for '/xblock' DELETE url."""
    def test_delete_static_page(self):
        # Add static tab
        resp = self.create_xblock(category='static_tab')
        self.assertEqual(resp.status_code, 200)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp_content = json.loads(resp.content)
        resp = self.client.delete('/xblock/' + resp_content['locator'])
        self.assertEqual(resp.status_code, 204)


class TestCreateItem(ItemTest):
    """
    Test the create_item handler thoroughly
    """
    def test_create_nicely(self):
        """
        Try the straightforward use cases
        """
        # create a chapter
        display_name = 'Nicely created'
        resp = self.create_xblock(display_name=display_name, category='chapter')
        self.assertEqual(resp.status_code, 200)

        # get the new item and check its category and display_name
        chap_locator = self.response_locator(resp)
        new_obj = self.get_item_from_modulestore(chap_locator)
        self.assertEqual(new_obj.scope_ids.block_type, 'chapter')
        self.assertEqual(new_obj.display_name, display_name)
        self.assertEqual(new_obj.location.org, self.course.location.org)
        self.assertEqual(new_obj.location.course, self.course.location.course)

        # get the course and ensure it now points to this one
        course = self.get_item_from_modulestore(self.unicode_locator)
        self.assertIn(self.get_old_id(chap_locator).url(), course.children)

        # use default display name
        resp = self.create_xblock(parent_locator=chap_locator, category='vertical')
        self.assertEqual(resp.status_code, 200)

        vert_locator = self.response_locator(resp)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.create_xblock(
            parent_locator=vert_locator,
            category='problem',
            boilerplate=template_id
        )
        self.assertEqual(resp.status_code, 200)
        prob_locator = self.response_locator(resp)
        problem = self.get_item_from_modulestore(prob_locator, True)
        # ensure it's draft
        self.assertTrue(problem.is_draft)
        # check against the template
        template = CapaDescriptor.get_template(template_id)
        self.assertEqual(problem.data, template['data'])
        self.assertEqual(problem.display_name, template['metadata']['display_name'])
        self.assertEqual(problem.markdown, template['metadata']['markdown'])

    def test_create_item_negative(self):
        """
        Negative tests for create_item
        """
        # non-existent boilerplate: creates a default
        resp = self.create_xblock(category='problem', boilerplate='nosuchboilerplate.yaml')
        self.assertEqual(resp.status_code, 200)


class TestEditItem(ItemTest):
    """
    Test xblock update.
    """
    def setUp(self):
        """ Creates the test course structure and a couple problems to 'edit'. """
        super(TestEditItem, self).setUp()
        # create a chapter
        display_name = 'chapter created'
        resp = self.create_xblock(display_name=display_name, category='chapter')
        chap_locator = self.response_locator(resp)
        resp = self.create_xblock(parent_locator=chap_locator, category='sequential')
        self.seq_locator = self.response_locator(resp)
        self.seq_update_url = '/xblock/' + self.seq_locator

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.create_xblock(parent_locator=self.seq_locator, category='problem', boilerplate=template_id)
        self.problem_locator = self.response_locator(resp)
        self.problem_update_url = '/xblock/' + self.problem_locator

        self.course_update_url = '/xblock/' + self.unicode_locator

    def test_delete_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': 'onreset'}}
        )
        problem = self.get_item_from_modulestore(self.problem_locator, True)
        self.assertEqual(problem.rerandomize, 'onreset')
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': None}}
        )
        problem = self.get_item_from_modulestore(self.problem_locator, True)
        self.assertEqual(problem.rerandomize, 'never')

    def test_null_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        problem = self.get_item_from_modulestore(self.problem_locator, True)
        self.assertIsNotNone(problem.markdown)
        self.client.ajax_post(
            self.problem_update_url,
            data={'nullout': ['markdown']}
        )
        problem = self.get_item_from_modulestore(self.problem_locator, True)
        self.assertIsNone(problem.markdown)

    def test_date_fields(self):
        """
        Test setting due & start dates on sequential
        """
        sequential = self.get_item_from_modulestore(self.seq_locator)
        self.assertIsNone(sequential.due)
        self.client.ajax_post(
            self.seq_update_url,
            data={'metadata': {'due': '2010-11-22T04:00Z'}}
        )
        sequential = self.get_item_from_modulestore(self.seq_locator)
        self.assertEqual(sequential.due, datetime.datetime(2010, 11, 22, 4, 0, tzinfo=UTC))
        self.client.ajax_post(
            self.seq_update_url,
            data={'metadata': {'start': '2010-09-12T14:00Z'}}
        )
        sequential = self.get_item_from_modulestore(self.seq_locator)
        self.assertEqual(sequential.due, datetime.datetime(2010, 11, 22, 4, 0, tzinfo=UTC))
        self.assertEqual(sequential.start, datetime.datetime(2010, 9, 12, 14, 0, tzinfo=UTC))

    def test_delete_child(self):
        """
        Test deleting a child.
        """
        # Create 2 children of main course.
        resp_1 = self.create_xblock(display_name='child 1', category='chapter')
        resp_2 = self.create_xblock(display_name='child 2', category='chapter')
        chapter1_locator = self.response_locator(resp_1)
        chapter2_locator = self.response_locator(resp_2)

        course = self.get_item_from_modulestore(self.unicode_locator)
        self.assertIn(self.get_old_id(chapter1_locator).url(), course.children)
        self.assertIn(self.get_old_id(chapter2_locator).url(), course.children)

        # Remove one child from the course.
        resp = self.client.ajax_post(
            self.course_update_url,
            data={'children': [chapter2_locator]}
        )
        self.assertEqual(resp.status_code, 200)

        # Verify that the child is removed.
        course = self.get_item_from_modulestore(self.unicode_locator)
        self.assertNotIn(self.get_old_id(chapter1_locator).url(), course.children)
        self.assertIn(self.get_old_id(chapter2_locator).url(), course.children)

    def test_reorder_children(self):
        """
        Test reordering children that can be in the draft store.
        """
        # Create 2 child units and re-order them. There was a bug about @draft getting added
        # to the IDs.
        unit_1_resp = self.create_xblock(parent_locator=self.seq_locator, category='vertical')
        unit_2_resp = self.create_xblock(parent_locator=self.seq_locator, category='vertical')
        unit1_locator = self.response_locator(unit_1_resp)
        unit2_locator = self.response_locator(unit_2_resp)

        # The sequential already has a child defined in the setUp (a problem).
        # Children must be on the sequential to reproduce the original bug,
        # as it is important that the parent (sequential) NOT be in the draft store.
        children = self.get_item_from_modulestore(self.seq_locator).children
        self.assertEqual(self.get_old_id(unit1_locator).url(), children[1])
        self.assertEqual(self.get_old_id(unit2_locator).url(), children[2])

        resp = self.client.ajax_post(
            self.seq_update_url,
            data={'children': [self.problem_locator, unit2_locator, unit1_locator]}
        )
        self.assertEqual(resp.status_code, 200)

        children = self.get_item_from_modulestore(self.seq_locator).children
        self.assertEqual(self.get_old_id(self.problem_locator).url(), children[0])
        self.assertEqual(self.get_old_id(unit1_locator).url(), children[2])
        self.assertEqual(self.get_old_id(unit2_locator).url(), children[1])
