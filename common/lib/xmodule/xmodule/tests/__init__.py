"""
unittests for xmodule

Run like this:

    paver test_lib -l common/lib/xmodule

"""

import json
import os
import pprint
import unittest

from mock import Mock
from path import path

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds, Scope

from xmodule.x_module import ModuleSystem, XModuleDescriptor, XModuleMixin
from xmodule.modulestore.inheritance import InheritanceMixin, own_metadata
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import PublishState, ModuleStoreEnum
from xmodule.modulestore.mongo.draft import DraftModuleStore
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES


MODULE_DIR = path(__file__).dirname()
# Location of common test DATA directory
# '../../../../edx-platform/common/test/data/'
DATA_DIR = MODULE_DIR.parent.parent.parent.parent / "test" / "data"


open_ended_grading_interface = {
    'url': 'blah/',
    'username': 'incorrect_user',
    'password': 'incorrect_pass',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller',
}


class TestModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem for testing
    """
    def handler_url(self, block, handler, suffix='', query='', thirdparty=False):
        return '{usage_id}/{handler}{suffix}?{query}'.format(
            usage_id=block.scope_ids.usage_id.to_deprecated_string(),
            handler=handler,
            suffix=suffix,
            query=query,
        )

    def local_resource_url(self, block, uri):
        return 'resource/{usage_id}/{uri}'.format(
            usage_id=block.scope_ids.usage_id.to_deprecated_string(),
            uri=uri,
        )


def get_test_system(course_id=SlashSeparatedCourseKey('org', 'course', 'run')):
    """
    Construct a test ModuleSystem instance.

    By default, the render_template() method simply returns the repr of the
    context it is passed.  You can override this behavior by monkey patching::

        system = get_test_system()
        system.render_template = my_render_func

    where `my_render_func` is a function of the form my_render_func(template, context).

    """
    return TestModuleSystem(
        static_url='/static',
        track_function=Mock(),
        get_module=Mock(),
        render_template=mock_render_template,
        replace_urls=str,
        user=Mock(is_staff=False),
        filestore=Mock(),
        debug=True,
        hostname="edx.org",
        xqueue={'interface': None, 'callback_url': '/', 'default_queuename': 'testqueue', 'waittime': 10, 'construct_callback' : Mock(side_effect="/")},
        node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
        anonymous_student_id='student',
        open_ended_grading_interface=open_ended_grading_interface,
        course_id=course_id,
        error_descriptor_class=ErrorDescriptor,
        get_user_role=Mock(is_staff=False),
        descriptor_runtime=get_test_descriptor_system(),
        user_location=Mock(),
    )


def get_test_descriptor_system():
    """
    Construct a test DescriptorSystem instance.
    """
    return MakoDescriptorSystem(
        load_item=Mock(),
        resources_fs=Mock(),
        error_tracker=Mock(),
        render_template=mock_render_template,
        mixins=(InheritanceMixin, XModuleMixin),
        field_data=DictFieldData({}),
    )


def mock_render_template(*args, **kwargs):
    """
    Pretty-print the args and kwargs.

    Allows us to not depend on any actual template rendering mechanism,
    while still returning a unicode object
    """
    return pprint.pformat((args, kwargs)).decode()


class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_class(self):
        vc = XModuleDescriptor.load_class('video')
        vc_str = "<class 'xmodule.video_module.video_module.VideoDescriptor'>"
        self.assertEqual(str(vc), vc_str)


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_field_data = {}

    def setUp(self):
        class EmptyClass:
            """Empty object."""
            url_name = ''
            category = 'test'

        self.system = get_test_system()
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        usage_key = self.system.course_id.make_usage_key(self.descriptor.category, 'test_loc')
        # ScopeIds has 4 fields: user_id, block_type, def_id, usage_id
        scope_ids = ScopeIds(1, self.descriptor.category, usage_key, usage_key)
        self.xmodule = self.xmodule_class(
            self.descriptor, self.system, DictFieldData(self.raw_field_data), scope_ids
        )

    def ajax_request(self, dispatch, data):
        """Call Xmodule.handle_ajax."""
        return json.loads(self.xmodule.handle_ajax(dispatch, data))


class CourseComparisonTest(unittest.TestCase):
    """
    Mixin that has methods for comparing courses for equality.
    """

    def setUp(self):
        self.field_exclusions = set()
        self.ignored_asset_keys = set()

    def exclude_field(self, usage_id, field_name):
        """
        Mark field ``field_name`` of expected block usage ``usage_id`` as ignored

        Args:
            usage_id (:class:`opaque_keys.edx.UsageKey` or ``None``). If ``None``, skip, this field in all blocks
            field_name (string): The name of the field to skip
        """
        self.field_exclusions.add((usage_id, field_name))

    def ignore_asset_key(self, key_name):
        """
        Add an asset key to the list of keys to be ignored when comparing assets.

        Args:
            key_name: The name of the key to ignore.
        """
        self.ignored_asset_keys.add(key_name)

    def assertCoursesEqual(self, expected_store, expected_course_key, actual_store, actual_course_key):
        """
        Assert that the courses identified by ``expected_course_key`` in ``expected_store`` and
        ``actual_course_key`` in ``actual_store`` are identical (ignore differences related
        owing to the course_keys being different).

        Any field value mentioned in ``self.field_exclusions`` by the key (usage_id, field_name)
        will be ignored for the purpose of equality checking.
        """
        # compare published
        expected_items = expected_store.get_items(expected_course_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        actual_items = actual_store.get_items(actual_course_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        self.assertGreater(len(expected_items), 0)
        self._assertCoursesEqual(expected_items, actual_items, actual_course_key)

        # compare draft
        if expected_store.get_modulestore_type(None) == ModuleStoreEnum.Type.split:
            revision = ModuleStoreEnum.RevisionOption.draft_only
        else:
            revision = None
        expected_items = expected_store.get_items(expected_course_key, revision=revision)
        if actual_store.get_modulestore_type(None) == ModuleStoreEnum.Type.split:
            revision = ModuleStoreEnum.RevisionOption.draft_only
        else:
            revision = None
        actual_items = actual_store.get_items(actual_course_key, revision=revision)
        self._assertCoursesEqual(expected_items, actual_items, actual_course_key, expect_drafts=True)

    def _assertCoursesEqual(self, expected_items, actual_items, actual_course_key, expect_drafts=False):
        self.assertEqual(len(expected_items), len(actual_items))

        actual_item_map = {
            item.location.block_id: item
            for item in actual_items
        }

        for expected_item in expected_items:
            actual_item_location = actual_course_key.make_usage_key(expected_item.category, expected_item.location.block_id)
            # split and old mongo use different names for the course root but we don't know which
            # modulestore actual's come from here; so, assume old mongo and if that fails, assume split
            if expected_item.location.category == 'course':
                actual_item_location = actual_item_location.replace(name=actual_item_location.run)
            actual_item = actual_item_map.get(actual_item_location.block_id)
            # must be split
            if actual_item is None and expected_item.location.category == 'course':
                actual_item_location = actual_item_location.replace(name='course')
                actual_item = actual_item_map.get(actual_item_location.block_id)
            self.assertIsNotNone(actual_item, u'cannot find {} in {}'.format(actual_item_location, actual_item_map))

            # compare fields
            self.assertEqual(expected_item.fields, actual_item.fields)

            for field_name in expected_item.fields:
                if (expected_item.scope_ids.usage_id, field_name) in self.field_exclusions:
                    continue

                if (None, field_name) in self.field_exclusions:
                    continue

                # Children are handled specially
                if field_name == 'children':
                    continue

                exp_value = getattr(expected_item, field_name)
                actual_value = getattr(actual_item, field_name)
                self.assertEqual(
                    exp_value,
                    actual_value,
                    "Field {!r} doesn't match between usages {} and {}: {!r} != {!r}".format(
                        field_name,
                        expected_item.scope_ids.usage_id,
                        actual_item.scope_ids.usage_id,
                        exp_value,
                        actual_value,
                    )
                )

            # compare children
            self.assertEqual(expected_item.has_children, actual_item.has_children)
            if expected_item.has_children:
                actual_course_key = actual_item.location.course_key.version_agnostic()
                expected_children = [
                    course1_item_child.location.map_into_course(actual_course_key)
                    for course1_item_child in expected_item.get_children()
                    # get_children was returning drafts for published parents :-(
                    if expect_drafts or not getattr(course1_item_child, 'is_draft', False)
                ]
                actual_children = [
                    item_child.location.version_agnostic()
                    for item_child in actual_item.get_children()
                    # get_children was returning drafts for published parents :-(
                    if expect_drafts or not getattr(item_child, 'is_draft', False)
                ]
                self.assertEqual(expected_children, actual_children)

    def assertAssetEqual(self, expected_course_key, expected_asset, actual_course_key, actual_asset):
        """
        Assert that two assets are equal, allowing for differences related to their being from different courses.
        """
        for key in self.ignored_asset_keys:
            if key in expected_asset:
                del expected_asset[key]
            if key in actual_asset:
                del actual_asset[key]

        expected_key = expected_asset.pop('asset_key')
        actual_key = actual_asset.pop('asset_key')
        self.assertEqual(expected_key.map_into_course(actual_course_key), actual_key)
        self.assertEqual(expected_key, actual_key.map_into_course(expected_course_key))

        expected_filename = expected_asset.pop('filename')
        actual_filename = actual_asset.pop('filename')
        self.assertEqual(expected_key.to_deprecated_string(), expected_filename)
        self.assertEqual(actual_key.to_deprecated_string(), actual_filename)
        self.assertEqual(expected_asset, actual_asset)

    def _assertAssetsEqual(self, expected_course_key, expected_assets, actual_course_key, actual_assets):  # pylint: disable=invalid-name
        """
        Private helper method for assertAssetsEqual
        """
        self.assertEqual(len(expected_assets), len(actual_assets))

        actual_assets_map = {asset['asset_key']: asset for asset in actual_assets}
        for expected_item in expected_assets:
            actual_item = actual_assets_map[expected_item['asset_key'].map_into_course(actual_course_key)]
            self.assertAssetEqual(expected_course_key, expected_item, actual_course_key, actual_item)

    def assertAssetsEqual(self, expected_store, expected_course_key, actual_store, actual_course_key):
        """
        Assert that the course assets identified by ``expected_course_key`` in ``expected_store`` and
        ``actual_course_key`` in ``actual_store`` are identical, allowing for differences related
        to their being from different course keys.
        """
        expected_content, expected_count = expected_store.get_all_content_for_course(expected_course_key)
        actual_content, actual_count = actual_store.get_all_content_for_course(actual_course_key)

        self.assertEqual(expected_count, actual_count)
        self._assertAssetsEqual(expected_course_key, expected_content, actual_course_key, actual_content)

        expected_thumbs = expected_store.get_all_content_thumbnails_for_course(expected_course_key)
        actual_thumbs = actual_store.get_all_content_thumbnails_for_course(actual_course_key)

        self._assertAssetsEqual(expected_course_key, expected_thumbs, actual_course_key, actual_thumbs)
