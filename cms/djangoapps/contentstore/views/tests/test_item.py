"""Tests for items views."""

import json
from datetime import datetime
import ddt

from mock import patch
from pytz import UTC
from webob import Response

from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from contentstore.utils import reverse_usage_url

from contentstore.views.component import component_handler

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import compute_publish_state, PublishState
from student.tests.factories import UserFactory
from xmodule.capa_module import CapaDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.keys import UsageKey
from xmodule.modulestore.locations import Location


class ItemTest(CourseTestCase):
    """ Base test class for create, save, and delete """
    def setUp(self):
        super(ItemTest, self).setUp()

        self.course_key = self.course.id
        self.usage_key = self.course.location

    @staticmethod
    def get_item_from_modulestore(usage_key, draft=False):
        """
        Get the item referenced by the UsageKey from the modulestore
        """
        store = modulestore('draft') if draft else modulestore('direct')
        return store.get_item(usage_key)

    def response_usage_key(self, response):
        """
        Get the UsageKey from the response payload and verify that the status_code was 200.
        :param response:
        """
        parsed = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        return UsageKey.from_string(parsed['locator'])

    def create_xblock(self, parent_usage_key=None, display_name=None, category=None, boilerplate=None):
        data = {
            'parent_locator': unicode(self.usage_key) if parent_usage_key is None else unicode(parent_usage_key),
            'category': category
        }
        if display_name is not None:
            data['display_name'] = display_name
        if boilerplate is not None:
            data['boilerplate'] = boilerplate
        return self.client.ajax_post(reverse('contentstore.views.xblock_handler'), json.dumps(data))


class GetItem(ItemTest):
    """Tests for '/xblock' GET url."""

    def _create_vertical(self, parent_usage_key=None):
        """
        Creates a vertical, returning its UsageKey.
        """
        resp = self.create_xblock(category='vertical', parent_usage_key=parent_usage_key)
        self.assertEqual(resp.status_code, 200)
        return self.response_usage_key(resp)

    def _get_container_preview(self, usage_key):
        """
        Returns the HTML and resources required for the xblock at the specified UsageKey
        """
        preview_url = reverse_usage_url("xblock_view_handler", usage_key, {'view_name': 'container_preview'})
        resp = self.client.get(preview_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)
        resp_content = json.loads(resp.content)
        html = resp_content['html']
        self.assertTrue(html)
        resources = resp_content['resources']
        self.assertIsNotNone(resources)
        return html, resources

    def test_get_vertical(self):
        # Add a vertical
        resp = self.create_xblock(category='vertical')
        usage_key = self.response_usage_key(resp)

        # Retrieve it
        resp = self.client.get(reverse_usage_url('xblock_handler', usage_key))
        self.assertEqual(resp.status_code, 200)

    def test_get_empty_container_fragment(self):
        root_usage_key = self._create_vertical()
        html, __ = self._get_container_preview(root_usage_key)

        # Verify that the Studio wrapper is not added
        self.assertNotIn('wrapper-xblock', html)

        # Verify that the header and article tags are still added
        self.assertIn('<header class="xblock-header">', html)
        self.assertIn('<article class="xblock-render">', html)

    def test_get_container_fragment(self):
        root_usage_key = self._create_vertical()

        # Add a problem beneath a child vertical
        child_vertical_usage_key = self._create_vertical(parent_usage_key=root_usage_key)
        resp = self.create_xblock(parent_usage_key=child_vertical_usage_key, category='problem', boilerplate='multiplechoice.yaml')
        self.assertEqual(resp.status_code, 200)

        # Get the preview HTML
        html, __ = self._get_container_preview(root_usage_key)

        # Verify that the Studio nesting wrapper has been added
        self.assertIn('level-nesting', html)
        self.assertIn('<header class="xblock-header">', html)
        self.assertIn('<article class="xblock-render">', html)

        # Verify that the Studio element wrapper has been added
        self.assertIn('level-element', html)

    def test_get_container_nested_container_fragment(self):
        """
        Test the case of the container page containing a link to another container page.
        """
        # Add a wrapper with child beneath a child vertical
        root_usage_key = self._create_vertical()

        resp = self.create_xblock(parent_usage_key=root_usage_key, category="wrapper")
        self.assertEqual(resp.status_code, 200)
        wrapper_usage_key = self.response_usage_key(resp)

        resp = self.create_xblock(parent_usage_key=wrapper_usage_key, category='problem', boilerplate='multiplechoice.yaml')
        self.assertEqual(resp.status_code, 200)

        # Get the preview HTML and verify the View -> link is present.
        html, __ = self._get_container_preview(root_usage_key)
        self.assertIn('wrapper-xblock', html)
        self.assertRegexpMatches(
            html,
            # The instance of the wrapper class will have an auto-generated ID. Allow any
            # characters after wrapper.
            (r'"/container/location:MITx\+999\+Robot_Super_Course\+wrapper\+\w+" class="action-button">\s*'
             '<span class="action-button-text">View</span>')
        )

    def test_split_test(self):
        """
        Test that a split_test module renders all of its children in Studio.
        """
        root_usage_key = self._create_vertical()
        resp = self.create_xblock(category='split_test', parent_usage_key=root_usage_key)
        split_test_usage_key = self.response_usage_key(resp)
        resp = self.create_xblock(parent_usage_key=split_test_usage_key, category='html', boilerplate='announcement.yaml')
        self.assertEqual(resp.status_code, 200)
        resp = self.create_xblock(parent_usage_key=split_test_usage_key, category='html', boilerplate='zooming_image.yaml')
        self.assertEqual(resp.status_code, 200)
        html, __ = self._get_container_preview(split_test_usage_key)
        self.assertIn('Announcement', html)
        self.assertIn('Zooming', html)


class DeleteItem(ItemTest):
    """Tests for '/xblock' DELETE url."""
    def test_delete_static_page(self):
        # Add static tab
        resp = self.create_xblock(category='static_tab')
        usage_key = self.response_usage_key(resp)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp = self.client.delete(reverse_usage_url('xblock_handler', usage_key))
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

        # get the new item and check its category and display_name
        chap_usage_key = self.response_usage_key(resp)
        new_obj = self.get_item_from_modulestore(chap_usage_key)
        self.assertEqual(new_obj.scope_ids.block_type, 'chapter')
        self.assertEqual(new_obj.display_name, display_name)
        self.assertEqual(new_obj.location.org, self.course.location.org)
        self.assertEqual(new_obj.location.course, self.course.location.course)

        # get the course and ensure it now points to this one
        course = self.get_item_from_modulestore(self.usage_key)
        self.assertIn(chap_usage_key, course.children)

        # use default display name
        resp = self.create_xblock(parent_usage_key=chap_usage_key, category='vertical')
        vert_usage_key = self.response_usage_key(resp)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.create_xblock(
            parent_usage_key=vert_usage_key,
            category='problem',
            boilerplate=template_id
        )
        prob_usage_key = self.response_usage_key(resp)
        problem = self.get_item_from_modulestore(prob_usage_key, True)
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

    def test_create_with_future_date(self):
        self.assertEqual(self.course.start, datetime(2030, 1, 1, tzinfo=UTC))
        resp = self.create_xblock(category='chapter')
        usage_key = self.response_usage_key(resp)
        obj = self.get_item_from_modulestore(usage_key)
        self.assertEqual(obj.start, datetime(2030, 1, 1, tzinfo=UTC))


class TestDuplicateItem(ItemTest):
    """
    Test the duplicate method.
    """
    def setUp(self):
        """ Creates the test course structure and a few components to 'duplicate'. """
        super(TestDuplicateItem, self).setUp()
        # Create a parent chapter (for testing children of children).
        resp = self.create_xblock(parent_usage_key=self.usage_key, category='chapter')
        self.chapter_usage_key = self.response_usage_key(resp)

        # create a sequential containing a problem and an html component
        resp = self.create_xblock(parent_usage_key=self.chapter_usage_key, category='sequential')
        self.seq_usage_key = self.response_usage_key(resp)

        # create problem and an html component
        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='problem', boilerplate='multiplechoice.yaml')
        self.problem_usage_key = self.response_usage_key(resp)

        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='html')
        self.html_usage_key = self.response_usage_key(resp)

        # Create a second sequential just (testing children of children)
        self.create_xblock(parent_usage_key=self.chapter_usage_key, category='sequential2')

    def test_duplicate_equality(self):
        """
        Tests that a duplicated xblock is identical to the original,
        except for location and display name.
        """
        def duplicate_and_verify(source_usage_key, parent_usage_key):
            usage_key = self._duplicate_item(parent_usage_key, source_usage_key)
            self.assertTrue(check_equality(source_usage_key, usage_key), "Duplicated item differs from original")

        def check_equality(source_usage_key, duplicate_usage_key):
            original_item = self.get_item_from_modulestore(source_usage_key, draft=True)
            duplicated_item = self.get_item_from_modulestore(duplicate_usage_key, draft=True)

            self.assertNotEqual(
                original_item.location,
                duplicated_item.location,
                "Location of duplicate should be different from original"
            )
            # Set the location and display name to be the same so we can make sure the rest of the duplicate is equal.
            duplicated_item.location = original_item.location
            duplicated_item.display_name = original_item.display_name

            # Children will also be duplicated, so for the purposes of testing equality, we will set
            # the children to the original after recursively checking the children.
            if original_item.has_children:
                self.assertEqual(
                    len(original_item.children),
                    len(duplicated_item.children),
                    "Duplicated item differs in number of children"
                )
                for i in xrange(len(original_item.children)):
                    if not check_equality(original_item.children[i], duplicated_item.children[i]):
                        return False
                duplicated_item.children = original_item.children

            return original_item == duplicated_item

        duplicate_and_verify(self.problem_usage_key, self.seq_usage_key)
        duplicate_and_verify(self.html_usage_key, self.seq_usage_key)
        duplicate_and_verify(self.seq_usage_key, self.chapter_usage_key)
        duplicate_and_verify(self.chapter_usage_key, self.usage_key)

    def test_ordering(self):
        """
        Tests the a duplicated xblock appears immediately after its source
        (if duplicate and source share the same parent), else at the
        end of the children of the parent.
        """
        def verify_order(source_usage_key, parent_usage_key, source_position=None):
            usage_key = self._duplicate_item(parent_usage_key, source_usage_key)
            parent = self.get_item_from_modulestore(parent_usage_key)
            children = parent.children
            if source_position is None:
                self.assertFalse(source_usage_key in children, 'source item not expected in children array')
                self.assertEqual(
                    children[len(children) - 1],
                    usage_key,
                    "duplicated item not at end"
                )
            else:
                self.assertEqual(
                    children[source_position],
                    source_usage_key,
                    "source item at wrong position"
                )
                self.assertEqual(
                    children[source_position + 1],
                    usage_key,
                    "duplicated item not ordered after source item"
                )

        verify_order(self.problem_usage_key, self.seq_usage_key, 0)
        # 2 because duplicate of problem should be located before.
        verify_order(self.html_usage_key, self.seq_usage_key, 2)
        verify_order(self.seq_usage_key, self.chapter_usage_key, 0)

        # Test duplicating something into a location that is not the parent of the original item.
        # Duplicated item should appear at the end.
        verify_order(self.html_usage_key, self.usage_key)

    def test_display_name(self):
        """
        Tests the expected display name for the duplicated xblock.
        """
        def verify_name(source_usage_key, parent_usage_key, expected_name, display_name=None):
            usage_key = self._duplicate_item(parent_usage_key, source_usage_key, display_name)
            duplicated_item = self.get_item_from_modulestore(usage_key, draft=True)
            self.assertEqual(duplicated_item.display_name, expected_name)
            return usage_key

        # Display name comes from template.
        dupe_usage_key = verify_name(self.problem_usage_key, self.seq_usage_key, "Duplicate of 'Multiple Choice'")
        # Test dupe of dupe.
        verify_name(dupe_usage_key, self.seq_usage_key, "Duplicate of 'Duplicate of 'Multiple Choice''")

        # Uses default display_name of 'Text' from HTML component.
        verify_name(self.html_usage_key, self.seq_usage_key, "Duplicate of 'Text'")

        # The sequence does not have a display_name set, so category is shown.
        verify_name(self.seq_usage_key, self.chapter_usage_key, "Duplicate of sequential")

        # Now send a custom display name for the duplicate.
        verify_name(self.seq_usage_key, self.chapter_usage_key, "customized name", display_name="customized name")

    def _duplicate_item(self, parent_usage_key, source_usage_key, display_name=None):
        data = {
            'parent_locator': unicode(parent_usage_key),
            'duplicate_source_locator': unicode(source_usage_key)
        }
        if display_name is not None:
            data['display_name'] = display_name

        resp = self.client.ajax_post(reverse('contentstore.views.xblock_handler'), json.dumps(data))
        return self.response_usage_key(resp)


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
        chap_usage_key = self.response_usage_key(resp)
        resp = self.create_xblock(parent_usage_key=chap_usage_key, category='sequential')
        self.seq_usage_key = self.response_usage_key(resp)
        self.seq_update_url = reverse_usage_url("xblock_handler", self.seq_usage_key)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='problem', boilerplate=template_id)
        self.problem_usage_key = self.response_usage_key(resp)
        self.problem_update_url = reverse_usage_url("xblock_handler", self.problem_usage_key)

        self.course_update_url = reverse_usage_url("xblock_handler", self.usage_key)

    def test_delete_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': 'onreset'}}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertEqual(problem.rerandomize, 'onreset')
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': None}}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertEqual(problem.rerandomize, 'never')

    def test_null_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        problem = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertIsNotNone(problem.markdown)
        self.client.ajax_post(
            self.problem_update_url,
            data={'nullout': ['markdown']}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertIsNone(problem.markdown)

    def test_date_fields(self):
        """
        Test setting due & start dates on sequential
        """
        sequential = self.get_item_from_modulestore(self.seq_usage_key)
        self.assertIsNone(sequential.due)
        self.client.ajax_post(
            self.seq_update_url,
            data={'metadata': {'due': '2010-11-22T04:00Z'}}
        )
        sequential = self.get_item_from_modulestore(self.seq_usage_key)
        self.assertEqual(sequential.due, datetime(2010, 11, 22, 4, 0, tzinfo=UTC))
        self.client.ajax_post(
            self.seq_update_url,
            data={'metadata': {'start': '2010-09-12T14:00Z'}}
        )
        sequential = self.get_item_from_modulestore(self.seq_usage_key)
        self.assertEqual(sequential.due, datetime(2010, 11, 22, 4, 0, tzinfo=UTC))
        self.assertEqual(sequential.start, datetime(2010, 9, 12, 14, 0, tzinfo=UTC))

    def test_delete_child(self):
        """
        Test deleting a child.
        """
        # Create 2 children of main course.
        resp_1 = self.create_xblock(display_name='child 1', category='chapter')
        resp_2 = self.create_xblock(display_name='child 2', category='chapter')
        chapter1_usage_key = self.response_usage_key(resp_1)
        chapter2_usage_key = self.response_usage_key(resp_2)

        course = self.get_item_from_modulestore(self.usage_key)
        self.assertIn(chapter1_usage_key, course.children)
        self.assertIn(chapter2_usage_key, course.children)

        # Remove one child from the course.
        resp = self.client.ajax_post(
            self.course_update_url,
            data={'children': [unicode(chapter2_usage_key)]}
        )
        self.assertEqual(resp.status_code, 200)

        # Verify that the child is removed.
        course = self.get_item_from_modulestore(self.usage_key)
        self.assertNotIn(chapter1_usage_key, course.children)
        self.assertIn(chapter2_usage_key, course.children)

    def test_reorder_children(self):
        """
        Test reordering children that can be in the draft store.
        """
        # Create 2 child units and re-order them. There was a bug about @draft getting added
        # to the IDs.
        unit_1_resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='vertical')
        unit_2_resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='vertical')
        unit1_usage_key = self.response_usage_key(unit_1_resp)
        unit2_usage_key = self.response_usage_key(unit_2_resp)

        # The sequential already has a child defined in the setUp (a problem).
        # Children must be on the sequential to reproduce the original bug,
        # as it is important that the parent (sequential) NOT be in the draft store.
        children = self.get_item_from_modulestore(self.seq_usage_key).children
        self.assertEqual(unit1_usage_key, children[1])
        self.assertEqual(unit2_usage_key, children[2])

        resp = self.client.ajax_post(
            self.seq_update_url,
            data={'children': [unicode(self.problem_usage_key), unicode(unit2_usage_key), unicode(unit1_usage_key)]}
        )
        self.assertEqual(resp.status_code, 200)

        children = self.get_item_from_modulestore(self.seq_usage_key).children
        self.assertEqual(self.problem_usage_key, children[0])
        self.assertEqual(unit1_usage_key, children[2])
        self.assertEqual(unit2_usage_key, children[1])

    def test_make_public(self):
        """ Test making a private problem public (publishing it). """
        # When the problem is first created, it is only in draft (because of its category).
        with self.assertRaises(ItemNotFoundError):
            self.get_item_from_modulestore(self.problem_usage_key, False)
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key, False))

    def test_make_private(self):
        """ Test making a public problem private (un-publishing it). """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key, False))
        # Now make it private
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_private'}
        )
        with self.assertRaises(ItemNotFoundError):
            self.get_item_from_modulestore(self.problem_usage_key, False)

    def test_make_draft(self):
        """ Test creating a draft version of a public problem. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key, False))
        # Now make it draft, which means both versions will exist.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'create_draft'}
        )
        # Update the draft version and check that published is different.
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'due': '2077-10-10T04:00Z'}}
        )
        published = self.get_item_from_modulestore(self.problem_usage_key, False)
        self.assertIsNone(published.due)
        draft = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertEqual(draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_make_public_with_update(self):
        """ Update a problem and make it public at the same time. """
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'make_public'
            }
        )
        published = self.get_item_from_modulestore(self.problem_usage_key, False)
        self.assertEqual(published.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_make_private_with_update(self):
        """ Make a problem private and update it at the same time. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'make_private'
            }
        )
        with self.assertRaises(ItemNotFoundError):
            self.get_item_from_modulestore(self.problem_usage_key, False)
        draft = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertEqual(draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_create_draft_with_update(self):
        """ Create a draft and update it at the same time. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key, False))
        # Now make it draft, which means both versions will exist.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'create_draft'
            }
        )
        published = self.get_item_from_modulestore(self.problem_usage_key, False)
        self.assertIsNone(published.due)
        draft = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertEqual(draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_published_and_draft_contents_with_update(self):
        """ Create a draft and publish it then modify the draft and check that published content is not modified """

        # Make problem public.
        resp = self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key, False))

        # Now make a draft
        resp = self.client.ajax_post(
            self.problem_update_url,
            data={
                'id': unicode(self.problem_usage_key),
                'metadata': {},
                'data': "<p>Problem content draft.</p>",
                'publish': 'create_draft'
            }
        )

        # Both published and draft content should be different
        published = self.get_item_from_modulestore(self.problem_usage_key, False)
        draft = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertNotEqual(draft.data, published.data)

        # Get problem by 'xblock_handler'
        view_url = reverse_usage_url("xblock_view_handler", self.problem_usage_key, {"view_name": "student_view"})
        resp = self.client.get(view_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)

        # Activate the editing view
        view_url = reverse_usage_url("xblock_view_handler", self.problem_usage_key, {"view_name": "studio_view"})
        resp = self.client.get(view_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)

        # Both published and draft content should still be different
        published = self.get_item_from_modulestore(self.problem_usage_key, False)
        draft = self.get_item_from_modulestore(self.problem_usage_key, True)
        self.assertNotEqual(draft.data, published.data)

    def test_publish_states_of_nested_xblocks(self):
        """ Test publishing of a unit page containing a nested xblock  """

        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, display_name='Test Unit', category='vertical')
        unit_usage_key = self.response_usage_key(resp)
        resp = self.create_xblock(parent_usage_key=unit_usage_key, category='wrapper')
        wrapper_usage_key = self.response_usage_key(resp)
        resp = self.create_xblock(parent_usage_key=wrapper_usage_key, category='html')
        html_usage_key = self.response_usage_key(resp)

        # The unit and its children should be private initially
        unit_update_url = reverse_usage_url('xblock_handler', unit_usage_key)
        unit = self.get_item_from_modulestore(unit_usage_key, True)
        html = self.get_item_from_modulestore(html_usage_key, True)
        self.assertEqual(compute_publish_state(unit), PublishState.private)
        self.assertEqual(compute_publish_state(html), PublishState.private)

        # Make the unit public and verify that the problem is also made public
        resp = self.client.ajax_post(
            unit_update_url,
            data={'publish': 'make_public'}
        )
        self.assertEqual(resp.status_code, 200)
        unit = self.get_item_from_modulestore(unit_usage_key, True)
        html = self.get_item_from_modulestore(html_usage_key, True)
        self.assertEqual(compute_publish_state(unit), PublishState.public)
        self.assertEqual(compute_publish_state(html), PublishState.public)

        # Make a draft for the unit and verify that the problem also has a draft
        resp = self.client.ajax_post(
            unit_update_url,
            data={
                'id': unicode(unit_usage_key),
                'metadata': {},
                'publish': 'create_draft'
            }
        )
        self.assertEqual(resp.status_code, 200)
        unit = self.get_item_from_modulestore(unit_usage_key, True)
        html = self.get_item_from_modulestore(html_usage_key, True)
        self.assertEqual(compute_publish_state(unit), PublishState.draft)
        self.assertEqual(compute_publish_state(html), PublishState.draft)


@ddt.ddt
class TestComponentHandler(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

        patcher = patch('contentstore.views.component.get_modulestore')
        self.get_modulestore = patcher.start()
        self.addCleanup(patcher.stop)

        self.descriptor = self.get_modulestore.return_value.get_item.return_value

        self.usage_key_string = unicode(
            Location('dummy_org', 'dummy_course', 'dummy_run', 'dummy_category', 'dummy_name')
        )

        self.user = UserFactory()

        self.request = self.request_factory.get('/dummy-url')
        self.request.user = self.user

    def test_invalid_handler(self):
        self.descriptor.handle.side_effect = Http404

        with self.assertRaises(Http404):
            component_handler(self.request, self.usage_key_string, 'invalid_handler')

    @ddt.data('GET', 'POST', 'PUT', 'DELETE')
    def test_request_method(self, method):

        def check_handler(handler, request, suffix):
            self.assertEquals(request.method, method)
            return Response()

        self.descriptor.handle = check_handler

        # Have to use the right method to create the request to get the HTTP method that we want
        req_factory_method = getattr(self.request_factory, method.lower())
        request = req_factory_method('/dummy-url')
        request.user = self.user

        component_handler(request, self.usage_key_string, 'dummy_handler')

    @ddt.data(200, 404, 500)
    def test_response_code(self, status_code):
        def create_response(handler, request, suffix):
            return Response(status_code=status_code)

        self.descriptor.handle = create_response

        self.assertEquals(component_handler(self.request, self.usage_key_string, 'dummy_handler').status_code, status_code)
