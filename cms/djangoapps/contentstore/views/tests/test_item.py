"""Tests for items views."""

import json
from datetime import datetime
import ddt

from mock import patch
from pytz import UTC
from unittest import skipUnless
from webob import Response

from django.conf import settings
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from contentstore.utils import reverse_usage_url, reverse_course_url

from contentstore.views.component import (
    component_handler, get_component_templates,
    SPLIT_TEST_COMPONENT_TYPE
)

from contentstore.tests.utils import CourseTestCase
from student.tests.factories import UserFactory
from xmodule.capa_module import CapaDescriptor
from xmodule.modulestore import PublishState
from xmodule.x_module import STUDIO_VIEW, STUDENT_VIEW
from xblock.exceptions import NoSuchHandlerError
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import Location
from xmodule.partitions.partitions import Group, UserPartition


class ItemTest(CourseTestCase):
    """ Base test class for create, save, and delete """
    def setUp(self):
        super(ItemTest, self).setUp()

        self.course_key = self.course.id
        self.usage_key = self.course.location

    def get_item_from_modulestore(self, usage_key, verify_is_draft=False):
        """
        Get the item referenced by the UsageKey from the modulestore
        """
        item = self.store.get_item(usage_key)
        if verify_is_draft:
            self.assertTrue(getattr(item, 'is_draft', False))
        return item

    def response_usage_key(self, response):
        """
        Get the UsageKey from the response payload and verify that the status_code was 200.
        :param response:
        """
        parsed = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        key = UsageKey.from_string(parsed['locator'])
        if key.course_key.run is None:
            key = key.map_into_course(CourseKey.from_string(parsed['courseKey']))
        return key

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

    def _create_vertical(self, parent_usage_key=None):
        """
        Creates a vertical, returning its UsageKey.
        """
        resp = self.create_xblock(category='vertical', parent_usage_key=parent_usage_key)
        self.assertEqual(resp.status_code, 200)
        return self.response_usage_key(resp)


class GetItem(ItemTest):
    """Tests for '/xblock' GET url."""

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
        self.assertIn('<header class="xblock-header xblock-header-vertical">', html)
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
        self.assertIn('<header class="xblock-header xblock-header-vertical">', html)
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
            (r'"/container/i4x://MITx/999/wrapper/\w+" class="action-button">\s*'
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
        problem = self.get_item_from_modulestore(prob_usage_key, verify_is_draft=True)
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
            original_item = self.get_item_from_modulestore(source_usage_key)
            duplicated_item = self.get_item_from_modulestore(duplicate_usage_key)

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
            duplicated_item = self.get_item_from_modulestore(usage_key)
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

    def verify_publish_state(self, usage_key, expected_publish_state):
        """
        Helper method that gets the item from the module store and verifies that the publish state is as expected.
        Returns the item corresponding to the given usage_key.
        """
        item = self.get_item_from_modulestore(
            usage_key,
            (expected_publish_state == PublishState.private) or (expected_publish_state == PublishState.draft)
        )
        self.assertEqual(expected_publish_state, self.store.compute_publish_state(item))
        return item

    def test_delete_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': 'onreset'}}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(problem.rerandomize, 'onreset')
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'rerandomize': None}}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(problem.rerandomize, 'never')

    def test_null_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        problem = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertIsNotNone(problem.markdown)
        self.client.ajax_post(
            self.problem_update_url,
            data={'nullout': ['markdown']}
        )
        problem = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
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
        self.verify_publish_state(self.problem_usage_key, PublishState.private)
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.public)

    def test_make_private(self):
        """ Test making a public problem private (un-publishing it). """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Now make it private
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_private'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.private)

    def test_make_draft(self):
        """ Test creating a draft version of a public problem. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        published = self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Now make it draft, which means both versions will exist.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'create_draft'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.draft)

        # Update the draft version and check that published is different.
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'due': '2077-10-10T04:00Z'}}
        )
        updated_draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(updated_draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))
        self.assertIsNone(published.due)

    def test_make_public_with_update(self):
        """ Update a problem and make it public at the same time. """
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'make_public'
            }
        )
        published = self.get_item_from_modulestore(self.problem_usage_key)
        self.assertEqual(published.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_make_private_with_update(self):
        """ Make a problem private and update it at the same time. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Make problem private and update.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'make_private'
            }
        )
        draft = self.verify_publish_state(self.problem_usage_key, PublishState.private)
        self.assertEqual(draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))

    def test_create_draft_with_update(self):
        """ Create a draft and update it at the same time. """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        published = self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Now make it draft, which means both versions will exist.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'metadata': {'due': '2077-10-10T04:00Z'},
                'publish': 'create_draft'
            }
        )
        draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))
        self.assertIsNone(published.due)

    def test_create_draft_with_multiple_requests(self):
        """
        Create a draft request returns already created version if it exists.
        """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Now make it draft, which means both versions will exist.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'create_draft'
            }
        )
        draft_1 = self.verify_publish_state(self.problem_usage_key, PublishState.draft)

        # Now check that when a user sends request to create a draft when there is already a draft version then
        # user gets that already created draft instead of getting 'DuplicateItemError' exception.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'create_draft'
            }
        )
        draft_2 = self.verify_publish_state(self.problem_usage_key, PublishState.draft)
        self.assertIsNotNone(draft_2)
        self.assertEqual(draft_1, draft_2)

    def test_make_private_with_multiple_requests(self):
        """
        Make private requests gets proper response even if xmodule is already made private.
        """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self.assertIsNotNone(self.get_item_from_modulestore(self.problem_usage_key))

        # Now make it private, and check that its version is private
        resp = self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'make_private'
            }
        )
        self.assertEqual(resp.status_code, 200)
        draft_1 = self.verify_publish_state(self.problem_usage_key, PublishState.private)

        # Now check that when a user sends request to make it private when it already is private then
        # user gets that private version instead of getting 'ItemNotFoundError' exception.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'make_private'
            }
        )
        self.assertEqual(resp.status_code, 200)
        draft_2 = self.verify_publish_state(self.problem_usage_key, PublishState.private)
        self.assertEqual(draft_1, draft_2)

    def test_published_and_draft_contents_with_update(self):
        """ Create a draft and publish it then modify the draft and check that published content is not modified """

        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        published = self.verify_publish_state(self.problem_usage_key, PublishState.public)

        # Now make a draft
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'id': unicode(self.problem_usage_key),
                'metadata': {},
                'data': "<p>Problem content draft.</p>",
                'publish': 'create_draft'
            }
        )

        # Both published and draft content should be different
        draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertNotEqual(draft.data, published.data)

        # Get problem by 'xblock_handler'
        view_url = reverse_usage_url("xblock_view_handler", self.problem_usage_key, {"view_name": STUDENT_VIEW})
        resp = self.client.get(view_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)

        # Activate the editing view
        view_url = reverse_usage_url("xblock_view_handler", self.problem_usage_key, {"view_name": STUDIO_VIEW})
        resp = self.client.get(view_url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 200)

        # Both published and draft content should still be different
        draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
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
        self.verify_publish_state(unit_usage_key, PublishState.private)
        self.verify_publish_state(html_usage_key, PublishState.private)

        # Make the unit public and verify that the problem is also made public
        resp = self.client.ajax_post(
            unit_update_url,
            data={'publish': 'make_public'}
        )
        self.assertEqual(resp.status_code, 200)
        self.verify_publish_state(unit_usage_key, PublishState.public)
        self.verify_publish_state(html_usage_key, PublishState.public)

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
        self.verify_publish_state(unit_usage_key, PublishState.draft)
        self.verify_publish_state(html_usage_key, PublishState.draft)


@skipUnless(settings.FEATURES.get('ENABLE_GROUP_CONFIGURATIONS'), 'Tests Group Configurations feature')
class TestEditSplitModule(ItemTest):
    """
    Tests around editing instances of the split_test module.
    """
    def setUp(self):
        super(TestEditSplitModule, self).setUp()
        self.course.user_partitions = [
            UserPartition(
                0, 'first_partition', 'First Partition',
                [Group("0", 'alpha'), Group("1", 'beta')]
            ),
            UserPartition(
                1, 'second_partition', 'Second Partition',
                [Group("0", 'Group 0'), Group("1", 'Group 1'), Group("2", 'Group 2')]
            )
        ]
        self.store.update_item(self.course, self.user.id)
        root_usage_key = self._create_vertical()
        resp = self.create_xblock(category='split_test', parent_usage_key=root_usage_key)
        self.split_test_usage_key = self.response_usage_key(resp)
        self.split_test_update_url = reverse_usage_url("xblock_handler", self.split_test_usage_key)
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/dummy-url')
        self.request.user = self.user

    def _update_partition_id(self, partition_id):
        """
        Helper method that sets the user_partition_id to the supplied value.

        The updated split_test instance is returned.
        """
        self.client.ajax_post(
            self.split_test_update_url,
            # Even though user_partition_id is Scope.content, it will get saved by the Studio editor as
            # metadata. The code in item.py will update the field correctly, even though it is not the
            # expected scope.
            data={'metadata': {'user_partition_id': str(partition_id)}}
        )

        # Verify the partition_id was saved.
        split_test = self.get_item_from_modulestore(self.split_test_usage_key, verify_is_draft=True)
        self.assertEqual(partition_id, split_test.user_partition_id)
        return split_test

    def _assert_children(self, expected_number):
        """
        Verifies the number of children of the split_test instance.
        """
        split_test = self.get_item_from_modulestore(self.split_test_usage_key, True)
        self.assertEqual(expected_number, len(split_test.children))
        return split_test

    def test_create_groups(self):
        """
        Test that verticals are created for the configuration groups when
        a spit test module is edited.
        """
        split_test = self.get_item_from_modulestore(self.split_test_usage_key, verify_is_draft=True)
        # Initially, no user_partition_id is set, and the split_test has no children.
        self.assertEqual(-1, split_test.user_partition_id)
        self.assertEqual(0, len(split_test.children))

        # Set the user_partition_id to 0.
        split_test = self._update_partition_id(0)

        # Verify that child verticals have been set to match the groups
        self.assertEqual(2, len(split_test.children))
        vertical_0 = self.get_item_from_modulestore(split_test.children[0], verify_is_draft=True)
        vertical_1 = self.get_item_from_modulestore(split_test.children[1], verify_is_draft=True)
        self.assertEqual("vertical", vertical_0.category)
        self.assertEqual("vertical", vertical_1.category)
        self.assertEqual("alpha", vertical_0.display_name)
        self.assertEqual("beta", vertical_1.display_name)

        # Verify that the group_id_to_child mapping is correct.
        self.assertEqual(2, len(split_test.group_id_to_child))
        self.assertEqual(vertical_0.location, split_test.group_id_to_child['0'])
        self.assertEqual(vertical_1.location, split_test.group_id_to_child['1'])

    def test_change_user_partition_id(self):
        """
        Test what happens when the user_partition_id is changed to a different groups
        group configuration.
        """
        # Set to first group configuration.
        split_test = self._update_partition_id(0)
        self.assertEqual(2, len(split_test.children))
        initial_vertical_0_location = split_test.children[0]
        initial_vertical_1_location = split_test.children[1]

        # Set to second group configuration
        split_test = self._update_partition_id(1)
        # We don't remove existing children.
        self.assertEqual(5, len(split_test.children))
        self.assertEqual(initial_vertical_0_location, split_test.children[0])
        self.assertEqual(initial_vertical_1_location, split_test.children[1])
        vertical_0 = self.get_item_from_modulestore(split_test.children[2], verify_is_draft=True)
        vertical_1 = self.get_item_from_modulestore(split_test.children[3], verify_is_draft=True)
        vertical_2 = self.get_item_from_modulestore(split_test.children[4], verify_is_draft=True)

        # Verify that the group_id_to child mapping is correct.
        self.assertEqual(3, len(split_test.group_id_to_child))
        self.assertEqual(vertical_0.location, split_test.group_id_to_child['0'])
        self.assertEqual(vertical_1.location, split_test.group_id_to_child['1'])
        self.assertEqual(vertical_2.location, split_test.group_id_to_child['2'])
        self.assertNotEqual(initial_vertical_0_location, vertical_0.location)
        self.assertNotEqual(initial_vertical_1_location, vertical_1.location)

    def test_change_same_user_partition_id(self):
        """
        Test that nothing happens when the user_partition_id is set to the same value twice.
        """
        # Set to first group configuration.
        split_test = self._update_partition_id(0)
        self.assertEqual(2, len(split_test.children))
        initial_group_id_to_child = split_test.group_id_to_child

        # Set again to first group configuration.
        split_test = self._update_partition_id(0)
        self.assertEqual(2, len(split_test.children))
        self.assertEqual(initial_group_id_to_child, split_test.group_id_to_child)

    def test_change_non_existent_user_partition_id(self):
        """
        Test that nothing happens when the user_partition_id is set to a value that doesn't exist.

        The user_partition_id will be updated, but children and group_id_to_child map will not change.
        """
        # Set to first group configuration.
        split_test = self._update_partition_id(0)
        self.assertEqual(2, len(split_test.children))
        initial_group_id_to_child = split_test.group_id_to_child

        # Set to an group configuration that doesn't exist.
        split_test = self._update_partition_id(-50)
        self.assertEqual(2, len(split_test.children))
        self.assertEqual(initial_group_id_to_child, split_test.group_id_to_child)

    def test_delete_children(self):
        """
        Test that deleting a child in the group_id_to_child map updates the map.

        Also test that deleting a child not in the group_id_to_child_map behaves properly.
        """
        # Set to first group configuration.
        self._update_partition_id(0)
        split_test = self._assert_children(2)
        vertical_1_usage_key = split_test.children[1]

        # Add an extra child to the split_test
        resp = self.create_xblock(category='html', parent_usage_key=self.split_test_usage_key)
        extra_child_usage_key = self.response_usage_key(resp)
        self._assert_children(3)

        # Remove the first child (which is part of the group configuration).
        resp = self.client.ajax_post(
            self.split_test_update_url,
            data={'children': [unicode(vertical_1_usage_key), unicode(extra_child_usage_key)]}
        )
        self.assertEqual(resp.status_code, 200)
        split_test = self._assert_children(2)

        # Check that group_id_to_child was updated appropriately
        group_id_to_child = split_test.group_id_to_child
        self.assertEqual(1, len(group_id_to_child))
        self.assertEqual(vertical_1_usage_key, group_id_to_child['1'])

        # Remove the "extra" child and make sure that group_id_to_child did not change.
        resp = self.client.ajax_post(
            self.split_test_update_url,
            data={'children': [unicode(vertical_1_usage_key)]}
        )
        self.assertEqual(resp.status_code, 200)
        split_test = self._assert_children(1)
        self.assertEqual(group_id_to_child, split_test.group_id_to_child)

    def test_add_groups(self):
        """
        Test the "fix up behavior" when groups are missing (after a group is added to a group configuration).

        This test actually belongs over in common, but it relies on a mutable modulestore.
        TODO: move tests that can go over to common after the mixed modulestore work is done.  # pylint: disable=fixme
        """
        # Set to first group configuration.
        split_test = self._update_partition_id(0)

        # Add a group to the first group configuration.
        split_test.user_partitions = [
            UserPartition(
                0, 'first_partition', 'First Partition',
                [Group("0", 'alpha'), Group("1", 'beta'), Group("2", 'pie')]
            )
        ]
        self.store.update_item(split_test, self.user.id)

        # group_id_to_child and children have not changed yet.
        split_test = self._assert_children(2)
        group_id_to_child = split_test.group_id_to_child
        self.assertEqual(2, len(group_id_to_child))

        # Call add_missing_groups method to add the missing group.
        split_test.add_missing_groups(self.request)
        split_test = self._assert_children(3)
        self.assertNotEqual(group_id_to_child, split_test.group_id_to_child)
        group_id_to_child = split_test.group_id_to_child
        self.assertEqual(split_test.children[2], group_id_to_child["2"])

        # Call add_missing_groups again -- it should be a no-op.
        split_test.add_missing_groups(self.request)
        split_test = self._assert_children(3)
        self.assertEqual(group_id_to_child, split_test.group_id_to_child)

    def test_view_index_ok(self):
        """
        Basic check that the groups configuration page responds correctly.
        """
        if SPLIT_TEST_COMPONENT_TYPE not in self.course.advanced_modules:
            self.course.advanced_modules.append(SPLIT_TEST_COMPONENT_TYPE)
            self.store.update_item(self.course, self.user.id)

        url = reverse_course_url('group_configurations_list_handler', self.course.id)
        resp = self.client.get(url)
        self.assertContains(resp, self.course.display_name)
        self.assertContains(resp, 'First Partition')
        self.assertContains(resp, 'alpha')
        self.assertContains(resp, 'Second Partition')
        self.assertContains(resp, 'Group 1')

    def test_view_index_disabled(self):
        """
        Check that group configuration page is not displayed when turned off.
        """
        if SPLIT_TEST_COMPONENT_TYPE in self.course.advanced_modules:
            self.course.advanced_modules.remove(SPLIT_TEST_COMPONENT_TYPE)
            self.store.update_item(self.course, self.user.id)

        url = reverse_course_url('group_configurations_list_handler', self.course.id)
        resp = self.client.get(url)
        self.assertContains(resp, "module is disabled")


@ddt.ddt
class TestComponentHandler(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

        patcher = patch('contentstore.views.component.modulestore')
        self.modulestore = patcher.start()
        self.addCleanup(patcher.stop)

        # component_handler calls modulestore.get_item to get the descriptor of the requested xBlock.
        # Here, we mock the return value of modulestore.get_item so it can be used to mock the handler
        # of the xBlock descriptor.
        self.descriptor = self.modulestore.return_value.get_item.return_value

        self.usage_key_string = unicode(
            Location('dummy_org', 'dummy_course', 'dummy_run', 'dummy_category', 'dummy_name')
        )

        self.user = UserFactory()

        self.request = self.request_factory.get('/dummy-url')
        self.request.user = self.user

    def test_invalid_handler(self):
        self.descriptor.handle.side_effect = NoSuchHandlerError

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


class TestComponentTemplates(CourseTestCase):
    """
    Unit tests for the generation of the component templates for a course.
    """

    def setUp(self):
        super(TestComponentTemplates, self).setUp()
        self.templates = get_component_templates(self.course)

    def get_templates_of_type(self, template_type):
        """
        Returns the templates for the specified type, or None if none is found.
        """
        template_dict = next((template for template in self.templates if template.get('type') == template_type), None)
        return template_dict.get('templates') if template_dict else None

    def get_template(self, templates, display_name):
        """
        Returns the template which has the specified display name.
        """
        return next((template for template in templates if template.get('display_name') == display_name), None)

    def test_basic_components(self):
        """
        Test the handling of the basic component templates.
        """
        self.assertIsNotNone(self.get_templates_of_type('discussion'))
        self.assertIsNotNone(self.get_templates_of_type('html'))
        self.assertIsNotNone(self.get_templates_of_type('problem'))
        self.assertIsNotNone(self.get_templates_of_type('video'))
        self.assertIsNone(self.get_templates_of_type('advanced'))

    def test_advanced_components(self):
        """
        Test the handling of advanced component templates.
        """
        self.course.advanced_modules.append('word_cloud')
        self.templates = get_component_templates(self.course)
        advanced_templates = self.get_templates_of_type('advanced')
        self.assertEqual(len(advanced_templates), 1)
        world_cloud_template = advanced_templates[0]
        self.assertEqual(world_cloud_template.get('category'), 'word_cloud')
        self.assertEqual(world_cloud_template.get('display_name'), u'Word cloud')
        self.assertIsNone(world_cloud_template.get('boilerplate_name', None))

        # Verify that non-advanced components are not added twice
        self.course.advanced_modules.append('video')
        self.course.advanced_modules.append('openassessment')
        self.templates = get_component_templates(self.course)
        advanced_templates = self.get_templates_of_type('advanced')
        self.assertEqual(len(advanced_templates), 1)
        only_template = advanced_templates[0]
        self.assertNotEqual(only_template.get('category'), 'video')
        self.assertNotEqual(only_template.get('category'), 'openassessment')

    def test_advanced_problems(self):
        """
        Test the handling of advanced problem templates.
        """
        problem_templates = self.get_templates_of_type('problem')
        ora_template = self.get_template(problem_templates, u'Peer Assessment')
        self.assertIsNotNone(ora_template)
        self.assertEqual(ora_template.get('category'), 'openassessment')
        self.assertIsNone(ora_template.get('boilerplate_name', None))
