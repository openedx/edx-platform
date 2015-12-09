"""Tests for items views."""
import json
from datetime import datetime, timedelta
import ddt

from mock import patch, Mock, PropertyMock
from pytz import UTC
from pyquery import PyQuery
from webob import Response

from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from contentstore.utils import reverse_usage_url, reverse_course_url

from contentstore.views.component import (
    component_handler, get_component_templates
)

from contentstore.views.item import (
    create_xblock_info, ALWAYS, VisibilityState, _xblock_type_and_display_name, add_container_page_publishing_info
)
from contentstore.tests.utils import CourseTestCase
from student.tests.factories import UserFactory
from xmodule.capa_module import CapaDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import ItemFactory, LibraryFactory, check_mongo_calls, CourseFactory
from xmodule.x_module import STUDIO_VIEW, STUDENT_VIEW
from xmodule.course_module import DEFAULT_START_DATE
from xblock.exceptions import NoSuchHandlerError
from xblock_django.user_service import DjangoXBlockUserService
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


@ddt.ddt
class GetItemTest(ItemTest):
    """Tests for '/xblock' GET url."""

    def _get_preview(self, usage_key, data=None):
        """ Makes a request to xblock preview handler """
        preview_url = reverse_usage_url("xblock_view_handler", usage_key, {'view_name': 'container_preview'})
        data = data if data else {}
        resp = self.client.get(preview_url, data, HTTP_ACCEPT='application/json')
        return resp

    def _get_container_preview(self, usage_key, data=None):
        """
        Returns the HTML and resources required for the xblock at the specified UsageKey
        """
        resp = self._get_preview(usage_key, data)
        self.assertEqual(resp.status_code, 200)
        resp_content = json.loads(resp.content)
        html = resp_content['html']
        self.assertTrue(html)
        resources = resp_content['resources']
        self.assertIsNotNone(resources)
        return html, resources

    def _get_container_preview_with_error(self, usage_key, expected_code, data=None, content_contains=None):
        """ Make request and asserts on response code and response contents """
        resp = self._get_preview(usage_key, data)
        self.assertEqual(resp.status_code, expected_code)
        if content_contains:
            self.assertIn(content_contains, resp.content)
        return resp

    @ddt.data(
        (1, 17, 15, 16, 12),
        (2, 17, 15, 16, 12),
        (3, 17, 15, 16, 12),
    )
    @ddt.unpack
    def test_get_query_count(self, branching_factor, chapter_queries, section_queries, unit_queries, problem_queries):
        self.populate_course(branching_factor)
        # Retrieve it
        with check_mongo_calls(chapter_queries):
            self.client.get(reverse_usage_url('xblock_handler', self.populated_usage_keys['chapter'][-1]))
        with check_mongo_calls(section_queries):
            self.client.get(reverse_usage_url('xblock_handler', self.populated_usage_keys['sequential'][-1]))
        with check_mongo_calls(unit_queries):
            self.client.get(reverse_usage_url('xblock_handler', self.populated_usage_keys['vertical'][-1]))
        with check_mongo_calls(problem_queries):
            self.client.get(reverse_usage_url('xblock_handler', self.populated_usage_keys['problem'][-1]))

    @ddt.data(
        (1, 30),
        (2, 32),
        (3, 34),
    )
    @ddt.unpack
    def test_container_get_query_count(self, branching_factor, unit_queries,):
        self.populate_course(branching_factor)
        with check_mongo_calls(unit_queries):
            self.client.get(reverse_usage_url('xblock_container_handler', self.populated_usage_keys['vertical'][-1]))

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

        # XBlock messages are added by the Studio wrapper.
        self.assertIn('wrapper-xblock-message', html)
        # Make sure that "wrapper-xblock" does not appear by itself (without -message at end).
        self.assertNotRegexpMatches(html, r'wrapper-xblock[^-]+')

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
            r'"/container/{}" class="action-button">\s*<span class="action-button-text">View</span>'.format(
                wrapper_usage_key
            )
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

    def test_split_test_edited(self):
        """
        Test that rename of a group changes display name of child vertical.
        """
        self.course.user_partitions = [UserPartition(
            0, 'first_partition', 'First Partition',
            [Group("0", 'alpha'), Group("1", 'beta')]
        )]
        self.store.update_item(self.course, self.user.id)
        root_usage_key = self._create_vertical()
        resp = self.create_xblock(category='split_test', parent_usage_key=root_usage_key)
        split_test_usage_key = self.response_usage_key(resp)
        self.client.ajax_post(
            reverse_usage_url("xblock_handler", split_test_usage_key),
            data={'metadata': {'user_partition_id': str(0)}}
        )
        html, __ = self._get_container_preview(split_test_usage_key)
        self.assertIn('alpha', html)
        self.assertIn('beta', html)

        # Rename groups in group configuration
        GROUP_CONFIGURATION_JSON = {
            u'id': 0,
            u'name': u'first_partition',
            u'scheme': u'random',
            u'description': u'First Partition',
            u'version': UserPartition.VERSION,
            u'groups': [
                {u'id': 0, u'name': u'New_NAME_A', u'version': 1},
                {u'id': 1, u'name': u'New_NAME_B', u'version': 1},
            ],
        }

        response = self.client.put(
            reverse_course_url('group_configurations_detail_handler', self.course.id, kwargs={'group_configuration_id': 0}),
            data=json.dumps(GROUP_CONFIGURATION_JSON),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        html, __ = self._get_container_preview(split_test_usage_key)
        self.assertNotIn('alpha', html)
        self.assertNotIn('beta', html)
        self.assertIn('New_NAME_A', html)
        self.assertIn('New_NAME_B', html)

    def test_valid_paging(self):
        """
        Tests that valid paging is passed along to underlying block
        """
        with patch('contentstore.views.item.get_preview_fragment') as patched_get_preview_fragment:
            retval = Mock()
            type(retval).content = PropertyMock(return_value="Some content")
            type(retval).resources = PropertyMock(return_value=[])
            patched_get_preview_fragment.return_value = retval

            root_usage_key = self._create_vertical()
            _, _ = self._get_container_preview(
                root_usage_key,
                {'enable_paging': 'true', 'page_number': 0, 'page_size': 2}
            )
            call_args = patched_get_preview_fragment.call_args[0]
            _, _, context = call_args
            self.assertIn('paging', context)
            self.assertEqual({'page_number': 0, 'page_size': 2}, context['paging'])

    @ddt.data([1, 'invalid'], ['invalid', 2])
    @ddt.unpack
    def test_invalid_paging(self, page_number, page_size):
        """
        Tests that valid paging is passed along to underlying block
        """
        root_usage_key = self._create_vertical()
        self._get_container_preview_with_error(
            root_usage_key,
            400,
            data={'enable_paging': 'true', 'page_number': page_number, 'page_size': page_size},
            content_contains="Couldn't parse paging parameters"
        )

    def test_get_user_partitions_and_groups(self):
        self.course.user_partitions = [
            UserPartition(
                id=0,
                name="Verification user partition",
                scheme=UserPartition.get_scheme("verification"),
                description="Verification user partition",
                groups=[
                    Group(id=0, name="Group A"),
                    Group(id=1, name="Group B"),
                ],
            ),
        ]
        self.store.update_item(self.course, self.user.id)

        # Create an item and retrieve it
        resp = self.create_xblock(category='vertical')
        usage_key = self.response_usage_key(resp)
        resp = self.client.get(reverse_usage_url('xblock_handler', usage_key))
        self.assertEqual(resp.status_code, 200)

        # Check that the partition and group information was returned
        result = json.loads(resp.content)
        self.assertEqual(result["user_partitions"], [
            {
                "id": 0,
                "name": "Verification user partition",
                "scheme": "verification",
                "groups": [
                    {
                        "id": 0,
                        "name": "Group A",
                        "selected": False,
                        "deleted": False,
                    },
                    {
                        "id": 1,
                        "name": "Group B",
                        "selected": False,
                        "deleted": False,
                    },
                ]
            }
        ])
        self.assertEqual(result["group_access"], {})


@ddt.ddt
class DeleteItem(ItemTest):
    """Tests for '/xblock' DELETE url."""
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_delete_static_page(self, store):
        course = CourseFactory.create(default_store=store)
        # Add static tab
        resp = self.create_xblock(category='static_tab', parent_usage_key=course.location)
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

    def test_static_tabs_initialization(self):
        """
        Test that static tab display names are not being initialized as None.
        """
        # Add a new static tab with no explicit name
        resp = self.create_xblock(category='static_tab')
        usage_key = self.response_usage_key(resp)

        # Check that its name is not None
        new_tab = self.get_item_from_modulestore(usage_key)
        self.assertEquals(new_tab.display_name, 'Empty')


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
            """ Duplicates the source, parenting to supplied parent. Then does equality check. """
            usage_key = self._duplicate_item(parent_usage_key, source_usage_key)
            self.assertTrue(
                check_equality(source_usage_key, usage_key, parent_usage_key),
                "Duplicated item differs from original"
            )

        def check_equality(source_usage_key, duplicate_usage_key, parent_usage_key=None):
            """
            Gets source and duplicated items from the modulestore using supplied usage keys.
            Then verifies that they represent equivalent items (modulo parents and other
            known things that may differ).
            """
            original_item = self.get_item_from_modulestore(source_usage_key)
            duplicated_item = self.get_item_from_modulestore(duplicate_usage_key)

            self.assertNotEqual(
                unicode(original_item.location),
                unicode(duplicated_item.location),
                "Location of duplicate should be different from original"
            )

            # Parent will only be equal for root of duplicated structure, in the case
            # where an item is duplicated in-place.
            if parent_usage_key and unicode(original_item.parent) == unicode(parent_usage_key):
                self.assertEqual(
                    unicode(parent_usage_key), unicode(duplicated_item.parent),
                    "Parent of duplicate should equal parent of source for root xblock when duplicated in-place"
                )
            else:
                self.assertNotEqual(
                    unicode(original_item.parent), unicode(duplicated_item.parent),
                    "Parent duplicate should be different from source"
                )

            # Set the location, display name, and parent to be the same so we can make sure the rest of the
            # duplicate is equal.
            duplicated_item.location = original_item.location
            duplicated_item.display_name = original_item.display_name
            duplicated_item.parent = original_item.parent

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


class TestEditItemSetup(ItemTest):
    """
    Setup for xblock update tests.
    """
    def setUp(self):
        """ Creates the test course structure and a couple problems to 'edit'. """
        super(TestEditItemSetup, self).setUp()
        # create a chapter
        display_name = 'chapter created'
        resp = self.create_xblock(display_name=display_name, category='chapter')
        chap_usage_key = self.response_usage_key(resp)

        # create 2 sequentials
        resp = self.create_xblock(parent_usage_key=chap_usage_key, category='sequential')
        self.seq_usage_key = self.response_usage_key(resp)
        self.seq_update_url = reverse_usage_url("xblock_handler", self.seq_usage_key)

        resp = self.create_xblock(parent_usage_key=chap_usage_key, category='sequential')
        self.seq2_usage_key = self.response_usage_key(resp)
        self.seq2_update_url = reverse_usage_url("xblock_handler", self.seq2_usage_key)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, category='problem', boilerplate=template_id)
        self.problem_usage_key = self.response_usage_key(resp)
        self.problem_update_url = reverse_usage_url("xblock_handler", self.problem_usage_key)

        self.course_update_url = reverse_usage_url("xblock_handler", self.usage_key)


class TestEditItem(TestEditItemSetup):
    """
    Test xblock update.
    """
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
        resp = self.client.delete(reverse_usage_url("xblock_handler", chapter1_usage_key))
        self.assertEqual(resp.status_code, 204)

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

    def test_move_parented_child(self):
        """
        Test moving a child from one Section to another
        """
        unit_1_key = self.response_usage_key(
            self.create_xblock(parent_usage_key=self.seq_usage_key, category='vertical', display_name='unit 1')
        )
        unit_2_key = self.response_usage_key(
            self.create_xblock(parent_usage_key=self.seq2_usage_key, category='vertical', display_name='unit 2')
        )

        # move unit 1 from sequential1 to sequential2
        resp = self.client.ajax_post(
            self.seq2_update_url,
            data={'children': [unicode(unit_1_key), unicode(unit_2_key)]}
        )
        self.assertEqual(resp.status_code, 200)

        # verify children
        self.assertListEqual(
            self.get_item_from_modulestore(self.seq2_usage_key).children,
            [unit_1_key, unit_2_key],
        )
        self.assertListEqual(
            self.get_item_from_modulestore(self.seq_usage_key).children,
            [self.problem_usage_key],  # problem child created in setUp
        )

    def test_move_orphaned_child_error(self):
        """
        Test moving an orphan returns an error
        """
        unit_1_key = self.store.create_item(self.user.id, self.course_key, 'vertical', 'unit1').location

        # adding orphaned unit 1 should return an error
        resp = self.client.ajax_post(
            self.seq2_update_url,
            data={'children': [unicode(unit_1_key)]}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid data, possibly caused by concurrent authors", resp.content)

        # verify children
        self.assertListEqual(
            self.get_item_from_modulestore(self.seq2_usage_key).children,
            []
        )

    def test_move_child_creates_orphan_error(self):
        """
        Test creating an orphan returns an error
        """
        unit_1_key = self.response_usage_key(
            self.create_xblock(parent_usage_key=self.seq2_usage_key, category='vertical', display_name='unit 1')
        )
        unit_2_key = self.response_usage_key(
            self.create_xblock(parent_usage_key=self.seq2_usage_key, category='vertical', display_name='unit 2')
        )

        # remove unit 2 should return an error
        resp = self.client.ajax_post(
            self.seq2_update_url,
            data={'children': [unicode(unit_1_key)]}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid data, possibly caused by concurrent authors", resp.content)

        # verify children
        self.assertListEqual(
            self.get_item_from_modulestore(self.seq2_usage_key).children,
            [unit_1_key, unit_2_key]
        )

    def _is_location_published(self, location):
        """
        Returns whether or not the item with given location has a published version.
        """
        return modulestore().has_item(location, revision=ModuleStoreEnum.RevisionOption.published_only)

    def _verify_published_with_no_draft(self, location):
        """
        Verifies the item with given location has a published version and no draft (unpublished changes).
        """
        self.assertTrue(self._is_location_published(location))
        self.assertFalse(modulestore().has_changes(modulestore().get_item(location)))

    def _verify_published_with_draft(self, location):
        """
        Verifies the item with given location has a published version and also a draft version (unpublished changes).
        """
        self.assertTrue(self._is_location_published(location))
        self.assertTrue(modulestore().has_changes(modulestore().get_item(location)))

    def test_make_public(self):
        """ Test making a private problem public (publishing it). """
        # When the problem is first created, it is only in draft (because of its category).
        self.assertFalse(self._is_location_published(self.problem_usage_key))
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self._verify_published_with_no_draft(self.problem_usage_key)

    def test_make_draft(self):
        """ Test creating a draft version of a public problem. """
        self._make_draft_content_different_from_published()

    def test_revert_to_published(self):
        """ Test reverting draft content to published """
        self._make_draft_content_different_from_published()
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'discard_changes'}
        )
        self._verify_published_with_no_draft(self.problem_usage_key)
        published = modulestore().get_item(self.problem_usage_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        self.assertIsNone(published.due)

    def test_republish(self):
        """ Test republishing an item. """
        new_display_name = 'New Display Name'

        # When the problem is first created, it is only in draft (because of its category).
        self.assertFalse(self._is_location_published(self.problem_usage_key))

        # Republishing when only in draft will update the draft but not cause a public item to be created.
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'republish',
                'metadata': {
                    'display_name': new_display_name
                }
            }
        )
        self.assertFalse(self._is_location_published(self.problem_usage_key))
        draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(draft.display_name, new_display_name)

        # Publish the item
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )

        # Now republishing should update the published version
        new_display_name_2 = 'New Display Name 2'
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'publish': 'republish',
                'metadata': {
                    'display_name': new_display_name_2
                }
            }
        )
        self._verify_published_with_no_draft(self.problem_usage_key)
        published = modulestore().get_item(
            self.problem_usage_key,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self.assertEqual(published.display_name, new_display_name_2)

    def test_direct_only_categories_not_republished(self):
        """Verify that republish is ignored for items in DIRECT_ONLY_CATEGORIES"""
        # Create a vertical child with published and unpublished versions.
        # If the parent sequential is not re-published, then the child problem should also not be re-published.
        resp = self.create_xblock(parent_usage_key=self.seq_usage_key, display_name='vertical', category='vertical')
        vertical_usage_key = self.response_usage_key(resp)
        vertical_update_url = reverse_usage_url('xblock_handler', vertical_usage_key)
        self.client.ajax_post(vertical_update_url, data={'publish': 'make_public'})
        self.client.ajax_post(vertical_update_url, data={'metadata': {'display_name': 'New Display Name'}})

        self._verify_published_with_draft(self.seq_usage_key)
        self.client.ajax_post(self.seq_update_url, data={'publish': 'republish'})
        self._verify_published_with_draft(self.seq_usage_key)

    def _make_draft_content_different_from_published(self):
        """
        Helper method to create different draft and published versions of a problem.
        """
        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self._verify_published_with_no_draft(self.problem_usage_key)
        published = modulestore().get_item(self.problem_usage_key, revision=ModuleStoreEnum.RevisionOption.published_only)

        # Update the draft version and check that published is different.
        self.client.ajax_post(
            self.problem_update_url,
            data={'metadata': {'due': '2077-10-10T04:00Z'}}
        )
        updated_draft = self.get_item_from_modulestore(self.problem_usage_key, verify_is_draft=True)
        self.assertEqual(updated_draft.due, datetime(2077, 10, 10, 4, 0, tzinfo=UTC))
        self.assertIsNone(published.due)
        # Fetch the published version again to make sure the due date is still unset.
        published = modulestore().get_item(published.location, revision=ModuleStoreEnum.RevisionOption.published_only)
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

    def test_published_and_draft_contents_with_update(self):
        """ Create a draft and publish it then modify the draft and check that published content is not modified """

        # Make problem public.
        self.client.ajax_post(
            self.problem_update_url,
            data={'publish': 'make_public'}
        )
        self._verify_published_with_no_draft(self.problem_usage_key)
        published = modulestore().get_item(self.problem_usage_key, revision=ModuleStoreEnum.RevisionOption.published_only)

        # Now make a draft
        self.client.ajax_post(
            self.problem_update_url,
            data={
                'id': unicode(self.problem_usage_key),
                'metadata': {},
                'data': "<p>Problem content draft.</p>"
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
        # Fetch the published version again to make sure the data is correct.
        published = modulestore().get_item(published.location, revision=ModuleStoreEnum.RevisionOption.published_only)
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
        self.assertFalse(self._is_location_published(unit_usage_key))
        self.assertFalse(self._is_location_published(html_usage_key))

        # Make the unit public and verify that the problem is also made public
        resp = self.client.ajax_post(
            unit_update_url,
            data={'publish': 'make_public'}
        )
        self.assertEqual(resp.status_code, 200)
        self._verify_published_with_no_draft(unit_usage_key)
        self._verify_published_with_no_draft(html_usage_key)

        # Make a draft for the unit and verify that the problem also has a draft
        resp = self.client.ajax_post(
            unit_update_url,
            data={
                'id': unicode(unit_usage_key),
                'metadata': {},
            }
        )
        self.assertEqual(resp.status_code, 200)
        self._verify_published_with_draft(unit_usage_key)
        self._verify_published_with_draft(html_usage_key)

    def test_field_value_errors(self):
        """
        Test that if the user's input causes a ValueError on an XBlock field,
        we provide a friendly error message back to the user.
        """
        response = self.create_xblock(parent_usage_key=self.seq_usage_key, category='video')
        video_usage_key = self.response_usage_key(response)
        update_url = reverse_usage_url('xblock_handler', video_usage_key)

        response = self.client.ajax_post(
            update_url,
            data={
                'id': unicode(video_usage_key),
                'metadata': {
                    'saved_video_position': "Not a valid relative time",
                },
            }
        )
        self.assertEqual(response.status_code, 400)
        parsed = json.loads(response.content)
        self.assertIn("error", parsed)
        self.assertIn("Incorrect RelativeTime value", parsed["error"])  # See xmodule/fields.py


class TestEditItemSplitMongo(TestEditItemSetup):
    """
    Tests for EditItem running on top of the SplitMongoModuleStore.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def test_editing_view_wrappers(self):
        """
        Verify that the editing view only generates a single wrapper, no matter how many times it's loaded

        Exposes: PLAT-417
        """
        view_url = reverse_usage_url("xblock_view_handler", self.problem_usage_key, {"view_name": STUDIO_VIEW})

        for __ in xrange(3):
            resp = self.client.get(view_url, HTTP_ACCEPT='application/json')
            self.assertEqual(resp.status_code, 200)
            content = json.loads(resp.content)
            self.assertEqual(len(PyQuery(content['html'])('.xblock-{}'.format(STUDIO_VIEW))), 1)


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
        self.assertEqual("Group ID 0", vertical_0.display_name)
        self.assertEqual("Group ID 1", vertical_1.display_name)

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
        group_id_to_child = split_test.group_id_to_child.copy()
        self.assertEqual(2, len(group_id_to_child))

        # Test environment and Studio use different module systems
        # (CachingDescriptorSystem is used in tests, PreviewModuleSystem in Studio).
        # CachingDescriptorSystem doesn't have user service, that's needed for
        # SplitTestModule. So, in this line of code we add this service manually.
        split_test.runtime._services['user'] = DjangoXBlockUserService(self.user)  # pylint: disable=protected-access

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


@ddt.ddt
class TestComponentHandler(TestCase):
    def setUp(self):
        super(TestComponentHandler, self).setUp()

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

    def test_advanced_components_without_display_name(self):
        """
        Test that advanced components without display names display their category instead.
        """
        self.course.advanced_modules.append('graphical_slider_tool')
        self.templates = get_component_templates(self.course)
        template = self.get_templates_of_type('advanced')[0]
        self.assertEqual(template.get('display_name'), 'graphical_slider_tool')

    def test_advanced_problems(self):
        """
        Test the handling of advanced problem templates.
        """
        problem_templates = self.get_templates_of_type('problem')
        ora_template = self.get_template(problem_templates, u'Peer Assessment')
        self.assertIsNotNone(ora_template)
        self.assertEqual(ora_template.get('category'), 'openassessment')
        self.assertIsNone(ora_template.get('boilerplate_name', None))

    @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ["combinedopenended", "peergrading"])
    def test_ora1_no_advance_component_button(self):
        """
        Test that there will be no `Advanced` button on unit page if `combinedopenended` and `peergrading` are
        deprecated provided that there are only 'combinedopenended', 'peergrading' modules in `Advanced Module List`
        """
        self.course.advanced_modules.extend(['combinedopenended', 'peergrading'])
        templates = get_component_templates(self.course)
        button_names = [template['display_name'] for template in templates]
        self.assertNotIn('Advanced', button_names)

    @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ["combinedopenended", "peergrading"])
    def test_cannot_create_ora1_problems(self):
        """
        Test that we can't create ORA1 problems if `combinedopenended` and `peergrading` are deprecated
        """
        self.course.advanced_modules.extend(['annotatable', 'combinedopenended', 'peergrading'])
        templates = get_component_templates(self.course)
        button_names = [template['display_name'] for template in templates]
        self.assertIn('Advanced', button_names)
        self.assertEqual(len(templates[0]['templates']), 1)
        template_display_names = [template['display_name'] for template in templates[0]['templates']]
        self.assertEqual(template_display_names, ['Annotation'])

    @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', [])
    def test_create_ora1_problems(self):
        """
        Test that we can create ORA1 problems if `combinedopenended` and `peergrading` are not deprecated
        """
        self.course.advanced_modules.extend(['annotatable', 'combinedopenended', 'peergrading'])
        templates = get_component_templates(self.course)
        button_names = [template['display_name'] for template in templates]
        self.assertIn('Advanced', button_names)
        self.assertEqual(len(templates[0]['templates']), 3)
        template_display_names = [template['display_name'] for template in templates[0]['templates']]
        self.assertEqual(template_display_names, ['Annotation', 'Open Response Assessment', 'Peer Grading Interface'])


@ddt.ddt
class TestXBlockInfo(ItemTest):
    """
    Unit tests for XBlock's outline handling.
    """
    def setUp(self):
        super(TestXBlockInfo, self).setUp()
        user_id = self.user.id
        self.chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Week 1", user_id=user_id
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name="Lesson 1", user_id=user_id
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Unit 1', user_id=user_id
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location, category='video', display_name='My Video', user_id=user_id
        )

    def test_json_responses(self):
        outline_url = reverse_usage_url('xblock_outline_handler', self.usage_key)
        resp = self.client.get(outline_url, HTTP_ACCEPT='application/json')
        json_response = json.loads(resp.content)
        self.validate_course_xblock_info(json_response, course_outline=True)

    @ddt.data(
        (ModuleStoreEnum.Type.split, 4, 4),
        (ModuleStoreEnum.Type.mongo, 5, 7),
    )
    @ddt.unpack
    def test_xblock_outline_handler_mongo_calls(self, store_type, chapter_queries, chapter_queries_1):
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            chapter = ItemFactory.create(
                parent_location=course.location, category='chapter', display_name='Week 1'
            )
            outline_url = reverse_usage_url('xblock_outline_handler', chapter.location)
            with check_mongo_calls(chapter_queries):
                self.client.get(outline_url, HTTP_ACCEPT='application/json')

            sequential = ItemFactory.create(
                parent_location=chapter.location, category='sequential', display_name='Sequential 1'
            )

            ItemFactory.create(
                parent_location=sequential.location, category='vertical', display_name='Vertical 1'
            )
            # calls should be same after adding two new children for split only.
            with check_mongo_calls(chapter_queries_1):
                self.client.get(outline_url, HTTP_ACCEPT='application/json')

    def test_entrance_exam_chapter_xblock_info(self):
        chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Entrance Exam",
            user_id=self.user.id, is_entrance_exam=True
        )
        chapter = modulestore().get_item(chapter.location)
        xblock_info = create_xblock_info(
            chapter,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )
        # entrance exam chapter should not be deletable, draggable and childAddable.
        actions = xblock_info['actions']
        self.assertEqual(actions['deletable'], False)
        self.assertEqual(actions['draggable'], False)
        self.assertEqual(actions['childAddable'], False)
        self.assertEqual(xblock_info['display_name'], 'Entrance Exam')
        self.assertIsNone(xblock_info.get('is_header_visible', None))

    def test_none_entrance_exam_chapter_xblock_info(self):
        chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Test Chapter",
            user_id=self.user.id
        )
        chapter = modulestore().get_item(chapter.location)
        xblock_info = create_xblock_info(
            chapter,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )

        # chapter should be deletable, draggable and childAddable if not an entrance exam.
        actions = xblock_info['actions']
        self.assertEqual(actions['deletable'], True)
        self.assertEqual(actions['draggable'], True)
        self.assertEqual(actions['childAddable'], True)
        # chapter xblock info should not contains the key of 'is_header_visible'.
        self.assertIsNone(xblock_info.get('is_header_visible', None))

    def test_entrance_exam_sequential_xblock_info(self):
        chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Entrance Exam",
            user_id=self.user.id, is_entrance_exam=True, in_entrance_exam=True
        )

        subsection = ItemFactory.create(
            parent_location=chapter.location, category='sequential', display_name="Subsection - Entrance Exam",
            user_id=self.user.id, in_entrance_exam=True
        )
        subsection = modulestore().get_item(subsection.location)
        xblock_info = create_xblock_info(
            subsection,
            include_child_info=True,
            include_children_predicate=ALWAYS
        )
        # in case of entrance exam subsection, header should be hidden.
        self.assertEqual(xblock_info['is_header_visible'], False)
        self.assertEqual(xblock_info['display_name'], 'Subsection - Entrance Exam')

    def test_none_entrance_exam_sequential_xblock_info(self):
        subsection = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name="Subsection - Exam",
            user_id=self.user.id
        )
        subsection = modulestore().get_item(subsection.location)
        xblock_info = create_xblock_info(
            subsection,
            include_child_info=True,
            include_children_predicate=ALWAYS,
            parent_xblock=self.chapter
        )
        # sequential xblock info should not contains the key of 'is_header_visible'.
        self.assertIsNone(xblock_info.get('is_header_visible', None))

    def test_chapter_xblock_info(self):
        chapter = modulestore().get_item(self.chapter.location)
        xblock_info = create_xblock_info(
            chapter,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )
        self.validate_chapter_xblock_info(xblock_info)

    def test_sequential_xblock_info(self):
        sequential = modulestore().get_item(self.sequential.location)
        xblock_info = create_xblock_info(
            sequential,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )
        self.validate_sequential_xblock_info(xblock_info)

    def test_vertical_xblock_info(self):
        vertical = modulestore().get_item(self.vertical.location)

        xblock_info = create_xblock_info(
            vertical,
            include_child_info=True,
            include_children_predicate=ALWAYS,
            include_ancestor_info=True,
            user=self.user
        )
        add_container_page_publishing_info(vertical, xblock_info)
        self.validate_vertical_xblock_info(xblock_info)

    def test_component_xblock_info(self):
        video = modulestore().get_item(self.video.location)
        xblock_info = create_xblock_info(
            video,
            include_child_info=True,
            include_children_predicate=ALWAYS
        )
        self.validate_component_xblock_info(xblock_info)

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_validate_start_date(self, store_type):
        """
        Validate if start-date year is less than 1900 reset the date to DEFAULT_START_DATE.
        """
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            chapter = ItemFactory.create(
                parent_location=course.location, category='chapter', display_name='Week 1'
            )

            chapter.start = datetime(year=1899, month=1, day=1, tzinfo=UTC)

            xblock_info = create_xblock_info(
                chapter,
                include_child_info=True,
                include_children_predicate=ALWAYS,
                include_ancestor_info=True,
                user=self.user
            )

            self.assertEqual(xblock_info['start'], DEFAULT_START_DATE.strftime('%Y-%m-%dT%H:%M:%SZ'))

    def validate_course_xblock_info(self, xblock_info, has_child_info=True, course_outline=False):
        """
        Validate that the xblock info is correct for the test course.
        """
        self.assertEqual(xblock_info['category'], 'course')
        self.assertEqual(xblock_info['id'], unicode(self.course.location))
        self.assertEqual(xblock_info['display_name'], self.course.display_name)
        self.assertTrue(xblock_info['published'])

        # Finally, validate the entire response for consistency
        self.validate_xblock_info_consistency(xblock_info, has_child_info=has_child_info, course_outline=course_outline)

    def validate_chapter_xblock_info(self, xblock_info, has_child_info=True):
        """
        Validate that the xblock info is correct for the test chapter.
        """
        self.assertEqual(xblock_info['category'], 'chapter')
        self.assertEqual(xblock_info['id'], unicode(self.chapter.location))
        self.assertEqual(xblock_info['display_name'], 'Week 1')
        self.assertTrue(xblock_info['published'])
        self.assertIsNone(xblock_info.get('edited_by', None))
        self.assertEqual(xblock_info['course_graders'], ['Homework', 'Lab', 'Midterm Exam', 'Final Exam'])
        self.assertEqual(xblock_info['start'], '2030-01-01T00:00:00Z')
        self.assertEqual(xblock_info['graded'], False)
        self.assertEqual(xblock_info['due'], None)
        self.assertEqual(xblock_info['format'], None)

        # Finally, validate the entire response for consistency
        self.validate_xblock_info_consistency(xblock_info, has_child_info=has_child_info)

    def validate_sequential_xblock_info(self, xblock_info, has_child_info=True):
        """
        Validate that the xblock info is correct for the test sequential.
        """
        self.assertEqual(xblock_info['category'], 'sequential')
        self.assertEqual(xblock_info['id'], unicode(self.sequential.location))
        self.assertEqual(xblock_info['display_name'], 'Lesson 1')
        self.assertTrue(xblock_info['published'])
        self.assertIsNone(xblock_info.get('edited_by', None))

        # Finally, validate the entire response for consistency
        self.validate_xblock_info_consistency(xblock_info, has_child_info=has_child_info)

    def validate_vertical_xblock_info(self, xblock_info):
        """
        Validate that the xblock info is correct for the test vertical.
        """
        self.assertEqual(xblock_info['category'], 'vertical')
        self.assertEqual(xblock_info['id'], unicode(self.vertical.location))
        self.assertEqual(xblock_info['display_name'], 'Unit 1')
        self.assertTrue(xblock_info['published'])
        self.assertEqual(xblock_info['edited_by'], 'testuser')

        # Validate that the correct ancestor info has been included
        ancestor_info = xblock_info.get('ancestor_info', None)
        self.assertIsNotNone(ancestor_info)
        ancestors = ancestor_info['ancestors']
        self.assertEqual(len(ancestors), 3)
        self.validate_sequential_xblock_info(ancestors[0], has_child_info=True)
        self.validate_chapter_xblock_info(ancestors[1], has_child_info=False)
        self.validate_course_xblock_info(ancestors[2], has_child_info=False)

        # Finally, validate the entire response for consistency
        self.validate_xblock_info_consistency(xblock_info, has_child_info=True, has_ancestor_info=True)

    def validate_component_xblock_info(self, xblock_info):
        """
        Validate that the xblock info is correct for the test component.
        """
        self.assertEqual(xblock_info['category'], 'video')
        self.assertEqual(xblock_info['id'], unicode(self.video.location))
        self.assertEqual(xblock_info['display_name'], 'My Video')
        self.assertTrue(xblock_info['published'])
        self.assertIsNone(xblock_info.get('edited_by', None))

        # Finally, validate the entire response for consistency
        self.validate_xblock_info_consistency(xblock_info)

    def validate_xblock_info_consistency(self, xblock_info, has_ancestor_info=False, has_child_info=False,
                                         course_outline=False):
        """
        Validate that the xblock info is internally consistent.
        """
        self.assertIsNotNone(xblock_info['display_name'])
        self.assertIsNotNone(xblock_info['id'])
        self.assertIsNotNone(xblock_info['category'])
        self.assertTrue(xblock_info['published'])
        if has_ancestor_info:
            self.assertIsNotNone(xblock_info.get('ancestor_info', None))
            ancestors = xblock_info['ancestor_info']['ancestors']
            for ancestor in xblock_info['ancestor_info']['ancestors']:
                self.validate_xblock_info_consistency(
                    ancestor,
                    has_child_info=(ancestor == ancestors[0]),    # Only the direct ancestor includes children
                    course_outline=course_outline
                )
        else:
            self.assertIsNone(xblock_info.get('ancestor_info', None))
        if has_child_info:
            self.assertIsNotNone(xblock_info.get('child_info', None))
            if xblock_info['child_info'].get('children', None):
                for child_response in xblock_info['child_info']['children']:
                    self.validate_xblock_info_consistency(
                        child_response,
                        has_child_info=(not child_response.get('child_info', None) is None),
                        course_outline=course_outline
                    )
        else:
            self.assertIsNone(xblock_info.get('child_info', None))

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True})
    def test_proctored_exam_xblock_info(self):
        self.course.enable_proctored_exams = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        course = modulestore().get_item(self.course.location)
        xblock_info = create_xblock_info(
            course,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )
        # exam proctoring should be enabled and time limited.
        self.assertEqual(xblock_info['enable_proctored_exams'], True)

        sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential',
            display_name="Test Lesson 1", user_id=self.user.id,
            is_proctored_exam=True, is_time_limited=True,
            default_time_limit_minutes=100
        )
        sequential = modulestore().get_item(sequential.location)
        xblock_info = create_xblock_info(
            sequential,
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )
        # exam proctoring should be enabled and time limited.
        self.assertEqual(xblock_info['is_proctored_exam'], True)
        self.assertEqual(xblock_info['is_time_limited'], True)
        self.assertEqual(xblock_info['default_time_limit_minutes'], 100)


class TestLibraryXBlockInfo(ModuleStoreTestCase):
    """
    Unit tests for XBlock Info for XBlocks in a content library
    """
    def setUp(self):
        super(TestLibraryXBlockInfo, self).setUp()
        user_id = self.user.id
        self.library = LibraryFactory.create()
        self.top_level_html = ItemFactory.create(
            parent_location=self.library.location, category='html', user_id=user_id, publish_item=False
        )
        self.vertical = ItemFactory.create(
            parent_location=self.library.location, category='vertical', user_id=user_id, publish_item=False
        )
        self.child_html = ItemFactory.create(
            parent_location=self.vertical.location, category='html', display_name='Test HTML Child Block',
            user_id=user_id, publish_item=False
        )

    def test_lib_xblock_info(self):
        html_block = modulestore().get_item(self.top_level_html.location)
        xblock_info = create_xblock_info(html_block)
        self.validate_component_xblock_info(xblock_info, html_block)
        self.assertIsNone(xblock_info.get('child_info', None))

    def test_lib_child_xblock_info(self):
        html_block = modulestore().get_item(self.child_html.location)
        xblock_info = create_xblock_info(html_block, include_ancestor_info=True, include_child_info=True)
        self.validate_component_xblock_info(xblock_info, html_block)
        self.assertIsNone(xblock_info.get('child_info', None))
        ancestors = xblock_info['ancestor_info']['ancestors']
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0]['category'], 'vertical')
        self.assertEqual(ancestors[0]['id'], unicode(self.vertical.location))
        self.assertEqual(ancestors[1]['category'], 'library')

    def validate_component_xblock_info(self, xblock_info, original_block):
        """
        Validate that the xblock info is correct for the test component.
        """
        self.assertEqual(xblock_info['category'], original_block.category)
        self.assertEqual(xblock_info['id'], unicode(original_block.location))
        self.assertEqual(xblock_info['display_name'], original_block.display_name)
        self.assertIsNone(xblock_info.get('has_changes', None))
        self.assertIsNone(xblock_info.get('published', None))
        self.assertIsNone(xblock_info.get('published_on', None))
        self.assertIsNone(xblock_info.get('graders', None))


class TestLibraryXBlockCreation(ItemTest):
    """
    Tests the adding of XBlocks to Library
    """
    def test_add_xblock(self):
        """
        Verify we can add an XBlock to a Library.
        """
        lib = LibraryFactory.create()
        self.create_xblock(parent_usage_key=lib.location, display_name='Test', category="html")
        lib = self.store.get_library(lib.location.library_key)
        self.assertTrue(lib.children)
        xblock_locator = lib.children[0]
        self.assertEqual(self.store.get_item(xblock_locator).display_name, 'Test')

    def test_no_add_discussion(self):
        """
        Verify we cannot add a discussion module to a Library.
        """
        lib = LibraryFactory.create()
        response = self.create_xblock(parent_usage_key=lib.location, display_name='Test', category='discussion')
        self.assertEqual(response.status_code, 400)
        lib = self.store.get_library(lib.location.library_key)
        self.assertFalse(lib.children)

    def test_no_add_advanced(self):
        lib = LibraryFactory.create()
        lib.advanced_modules = ['lti']
        lib.save()
        response = self.create_xblock(parent_usage_key=lib.location, display_name='Test', category='lti')
        self.assertEqual(response.status_code, 400)
        lib = self.store.get_library(lib.location.library_key)
        self.assertFalse(lib.children)


class TestXBlockPublishingInfo(ItemTest):
    """
    Unit tests for XBlock's outline handling.
    """
    FIRST_SUBSECTION_PATH = [0]
    FIRST_UNIT_PATH = [0, 0]
    SECOND_UNIT_PATH = [0, 1]

    def _create_child(self, parent, category, display_name, publish_item=False, staff_only=False):
        """
        Creates a child xblock for the given parent.
        """
        child = ItemFactory.create(
            parent_location=parent.location, category=category, display_name=display_name,
            user_id=self.user.id, publish_item=publish_item
        )
        if staff_only:
            self._enable_staff_only(child.location)
        # In case the staff_only state was set, return the updated xblock.
        return modulestore().get_item(child.location)

    def _get_child_xblock_info(self, xblock_info, index):
        """
        Returns the child xblock info at the specified index.
        """
        children = xblock_info['child_info']['children']
        self.assertTrue(len(children) > index)
        return children[index]

    def _get_xblock_info(self, location):
        """
        Returns the xblock info for the specified location.
        """
        return create_xblock_info(
            modulestore().get_item(location),
            include_child_info=True,
            include_children_predicate=ALWAYS,
        )

    def _get_xblock_outline_info(self, location):
        """
        Returns the xblock info for the specified location as neeeded for the course outline page.
        """
        return create_xblock_info(
            modulestore().get_item(location),
            include_child_info=True,
            include_children_predicate=ALWAYS,
            course_outline=True
        )

    def _set_release_date(self, location, start):
        """
        Sets the release date for the specified xblock.
        """
        xblock = modulestore().get_item(location)
        xblock.start = start
        self.store.update_item(xblock, self.user.id)

    def _enable_staff_only(self, location):
        """
        Enables staff only for the specified xblock.
        """
        xblock = modulestore().get_item(location)
        xblock.visible_to_staff_only = True
        self.store.update_item(xblock, self.user.id)

    def _set_display_name(self, location, display_name):
        """
        Sets the display name for the specified xblock.
        """
        xblock = modulestore().get_item(location)
        xblock.display_name = display_name
        self.store.update_item(xblock, self.user.id)

    def _verify_xblock_info_state(self, xblock_info, xblock_info_field, expected_state, path=None, should_equal=True):
        """
        Verify the state of an xblock_info field. If no path is provided then the root item will be verified.
        If should_equal is True, assert that the current state matches the expected state, otherwise assert that they
        do not match.
        """
        if path:
            direct_child_xblock_info = self._get_child_xblock_info(xblock_info, path[0])
            remaining_path = path[1:] if len(path) > 1 else None
            self._verify_xblock_info_state(direct_child_xblock_info, xblock_info_field, expected_state, remaining_path, should_equal)
        else:
            if should_equal:
                self.assertEqual(xblock_info[xblock_info_field], expected_state)
            else:
                self.assertNotEqual(xblock_info[xblock_info_field], expected_state)

    def _verify_has_staff_only_message(self, xblock_info, expected_state, path=None):
        """
        Verify the staff_only_message field of xblock_info.
        """
        self._verify_xblock_info_state(xblock_info, 'staff_only_message', expected_state, path)

    def _verify_visibility_state(self, xblock_info, expected_state, path=None, should_equal=True):
        """
        Verify the publish state of an item in the xblock_info.
        """
        self._verify_xblock_info_state(xblock_info, 'visibility_state', expected_state, path, should_equal)

    def _verify_explicit_staff_lock_state(self, xblock_info, expected_state, path=None, should_equal=True):
        """
        Verify the explicit staff lock state of an item in the xblock_info.
        """
        self._verify_xblock_info_state(xblock_info, 'has_explicit_staff_lock', expected_state, path, should_equal)

    def test_empty_chapter(self):
        empty_chapter = self._create_child(self.course, 'chapter', "Empty Chapter")
        xblock_info = self._get_xblock_info(empty_chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.unscheduled)

    def test_empty_sequential(self):
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        self._create_child(chapter, 'sequential', "Empty Sequential")
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.unscheduled)
        self._verify_visibility_state(xblock_info, VisibilityState.unscheduled, path=self.FIRST_SUBSECTION_PATH)

    def test_published_unit(self):
        """
        Tests the visibility state of a published unit with release date in the future.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(chapter.location, datetime.now(UTC) + timedelta(days=1))
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.ready)
        self._verify_visibility_state(xblock_info, VisibilityState.ready, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.ready, path=self.FIRST_UNIT_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.SECOND_UNIT_PATH)

    def test_released_unit(self):
        """
        Tests the visibility state of a published unit with release date in the past.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(chapter.location, datetime.now(UTC) - timedelta(days=1))
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.live)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_UNIT_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.SECOND_UNIT_PATH)

    def test_unpublished_changes(self):
        """
        Tests the visibility state of a published unit with draft (unpublished) changes.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        unit = self._create_child(sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(sequential, 'vertical', "Staff Only Unit", staff_only=True)
        # Setting the display name creates a draft version of unit.
        self._set_display_name(unit.location, 'Updated Unit')
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.needs_attention)
        self._verify_visibility_state(xblock_info, VisibilityState.needs_attention, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.needs_attention, path=self.FIRST_UNIT_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.SECOND_UNIT_PATH)

    def test_partially_released_section(self):
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        released_sequential = self._create_child(chapter, 'sequential', "Released Sequential")
        self._create_child(released_sequential, 'vertical', "Released Unit", publish_item=True)
        self._create_child(released_sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(chapter.location, datetime.now(UTC) - timedelta(days=1))
        published_sequential = self._create_child(chapter, 'sequential', "Published Sequential")
        self._create_child(published_sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(published_sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(published_sequential.location, datetime.now(UTC) + timedelta(days=1))
        xblock_info = self._get_xblock_info(chapter.location)

        # Verify the state of the released sequential
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=[0])
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=[0, 0])
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=[0, 1])

        # Verify the state of the published sequential
        self._verify_visibility_state(xblock_info, VisibilityState.ready, path=[1])
        self._verify_visibility_state(xblock_info, VisibilityState.ready, path=[1, 0])
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=[1, 1])

        # Finally verify the state of the chapter
        self._verify_visibility_state(xblock_info, VisibilityState.ready)

    def test_staff_only_section(self):
        """
        Tests that an explicitly staff-locked section and all of its children are visible to staff only.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter", staff_only=True)
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        vertical = self._create_child(sequential, 'vertical', "Unit")
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_UNIT_PATH)

        self._verify_explicit_staff_lock_state(xblock_info, True)
        self._verify_explicit_staff_lock_state(xblock_info, False, path=self.FIRST_SUBSECTION_PATH)
        self._verify_explicit_staff_lock_state(xblock_info, False, path=self.FIRST_UNIT_PATH)

        vertical_info = self._get_xblock_info(vertical.location)
        add_container_page_publishing_info(vertical, vertical_info)
        self.assertEqual(_xblock_type_and_display_name(chapter), vertical_info["staff_lock_from"])

    def test_no_staff_only_section(self):
        """
        Tests that a section with a staff-locked subsection and a visible subsection is not staff locked itself.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        self._create_child(chapter, 'sequential', "Test Visible Sequential")
        self._create_child(chapter, 'sequential', "Test Staff Locked Sequential", staff_only=True)
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, should_equal=False)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=[0], should_equal=False)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=[1])

    def test_staff_only_subsection(self):
        """
        Tests that an explicitly staff-locked subsection and all of its children are visible to staff only.
        In this case the parent section is also visible to staff only because all of its children are staff only.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential", staff_only=True)
        vertical = self._create_child(sequential, 'vertical', "Unit")
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_UNIT_PATH)

        self._verify_explicit_staff_lock_state(xblock_info, False)
        self._verify_explicit_staff_lock_state(xblock_info, True, path=self.FIRST_SUBSECTION_PATH)
        self._verify_explicit_staff_lock_state(xblock_info, False, path=self.FIRST_UNIT_PATH)

        vertical_info = self._get_xblock_info(vertical.location)
        add_container_page_publishing_info(vertical, vertical_info)
        self.assertEqual(_xblock_type_and_display_name(sequential), vertical_info["staff_lock_from"])

    def test_no_staff_only_subsection(self):
        """
        Tests that a subsection with a staff-locked unit and a visible unit is not staff locked itself.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Unit")
        self._create_child(sequential, 'vertical', "Locked Unit", staff_only=True)
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, self.FIRST_SUBSECTION_PATH, should_equal=False)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, self.FIRST_UNIT_PATH, should_equal=False)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, self.SECOND_UNIT_PATH)

    def test_staff_only_unit(self):
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        vertical = self._create_child(sequential, 'vertical', "Unit", staff_only=True)
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.FIRST_UNIT_PATH)

        self._verify_explicit_staff_lock_state(xblock_info, False)
        self._verify_explicit_staff_lock_state(xblock_info, False, path=self.FIRST_SUBSECTION_PATH)
        self._verify_explicit_staff_lock_state(xblock_info, True, path=self.FIRST_UNIT_PATH)

        vertical_info = self._get_xblock_info(vertical.location)
        add_container_page_publishing_info(vertical, vertical_info)
        self.assertEqual(_xblock_type_and_display_name(vertical), vertical_info["staff_lock_from"])

    def test_unscheduled_section_with_live_subsection(self):
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(sequential.location, datetime.now(UTC) - timedelta(days=1))
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.needs_attention)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_UNIT_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.SECOND_UNIT_PATH)

    def test_unreleased_section_with_live_subsection(self):
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Published Unit", publish_item=True)
        self._create_child(sequential, 'vertical', "Staff Only Unit", staff_only=True)
        self._set_release_date(chapter.location, datetime.now(UTC) + timedelta(days=1))
        self._set_release_date(sequential.location, datetime.now(UTC) - timedelta(days=1))
        xblock_info = self._get_xblock_info(chapter.location)
        self._verify_visibility_state(xblock_info, VisibilityState.needs_attention)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_SUBSECTION_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.live, path=self.FIRST_UNIT_PATH)
        self._verify_visibility_state(xblock_info, VisibilityState.staff_only, path=self.SECOND_UNIT_PATH)

    def test_locked_section_staff_only_message(self):
        """
        Tests that a locked section has a staff only message and its descendants do not.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter", staff_only=True)
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Unit")
        xblock_info = self._get_xblock_outline_info(chapter.location)
        self._verify_has_staff_only_message(xblock_info, True)
        self._verify_has_staff_only_message(xblock_info, False, path=self.FIRST_SUBSECTION_PATH)
        self._verify_has_staff_only_message(xblock_info, False, path=self.FIRST_UNIT_PATH)

    def test_locked_unit_staff_only_message(self):
        """
        Tests that a lone locked unit has a staff only message along with its ancestors.
        """
        chapter = self._create_child(self.course, 'chapter', "Test Chapter")
        sequential = self._create_child(chapter, 'sequential', "Test Sequential")
        self._create_child(sequential, 'vertical', "Unit", staff_only=True)
        xblock_info = self._get_xblock_outline_info(chapter.location)
        self._verify_has_staff_only_message(xblock_info, True)
        self._verify_has_staff_only_message(xblock_info, True, path=self.FIRST_SUBSECTION_PATH)
        self._verify_has_staff_only_message(xblock_info, True, path=self.FIRST_UNIT_PATH)
