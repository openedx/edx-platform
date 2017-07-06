""" Tests for DiscussionXBLock"""
from collections import namedtuple
import ddt
import itertools
import mock
from nose.plugins.attrib import attr
import random
import string
from unittest import TestCase

from safe_lxml import etree

from openedx.core.lib.xblock_builtin.xblock_discussion.xblock_discussion import DiscussionXBlock
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds, UNIQUE_ID, NO_CACHE_VALUE
from xblock.runtime import Runtime


AttributePair = namedtuple("AttributePair", ["name", "value"])


ID_ATTR_NAMES = ("discussion_id", "id",)
CATEGORY_ATTR_NAMES = ("discussion_category",)
TARGET_ATTR_NAMES = ("discussion_target", "for", )


def _random_string():
    """
    Generates random string
    """
    return ''.join(random.choice(string.lowercase, ) for _ in xrange(12))


def _make_attribute_test_cases():
    """
    Builds test cases for attribute-dependent tests
    """
    attribute_names = itertools.product(ID_ATTR_NAMES, CATEGORY_ATTR_NAMES, TARGET_ATTR_NAMES)
    for id_attr, category_attr, target_attr in attribute_names:
        yield (
            AttributePair(id_attr, _random_string()),
            AttributePair(category_attr, _random_string()),
            AttributePair(target_attr, _random_string())
        )


@attr('shard2')
@ddt.ddt
class DiscussionXBlockImportExportTests(TestCase):
    """
    Import and export tests
    """
    DISCUSSION_XBLOCK_LOCATION = "openedx.core.lib.xblock_builtin.xblock_discussion.xblock_discussion.DiscussionXBlock"

    def setUp(self):
        """
        Set up method
        """
        super(DiscussionXBlockImportExportTests, self).setUp()
        self.keys = ScopeIds("any_user", "discussion", "def_id", "usage_id")
        self.runtime_mock = mock.Mock(spec=Runtime)
        self.runtime_mock.construct_xblock_from_class = mock.Mock(side_effect=self._construct_xblock_mock)
        self.runtime_mock.get_policy = mock.Mock(return_value={})
        self.id_gen_mock = mock.Mock()

    def _construct_xblock_mock(self, cls, keys):  # pylint: disable=unused-argument
        """
        Builds target xblock instance (DiscussionXBlock)

        Signature-compatible with runtime.construct_xblock_from_class - can be used as a mock side-effect
        """
        return DiscussionXBlock(self.runtime_mock, scope_ids=keys, field_data=DictFieldData({}))

    @mock.patch(DISCUSSION_XBLOCK_LOCATION + ".load_definition_xml")
    @ddt.unpack
    @ddt.data(*list(_make_attribute_test_cases()))
    def test_xblock_export_format(self, id_pair, category_pair, target_pair, patched_load_definition_xml):
        """
        Test that xblock export XML format can be parsed preserving field values
        """
        xblock_xml = """
        <discussion
            url_name="82bb87a2d22240b1adac2dfcc1e7e5e4" xblock-family="xblock.v1"
            {id_attr}="{id_value}"
            {category_attr}="{category_value}"
            {target_attr}="{target_value}"
        />
        """.format(
            id_attr=id_pair.name, id_value=id_pair.value,
            category_attr=category_pair.name, category_value=category_pair.value,
            target_attr=target_pair.name, target_value=target_pair.value,
        )
        node = etree.fromstring(xblock_xml)

        patched_load_definition_xml.side_effect = Exception("Irrelevant")

        block = DiscussionXBlock.parse_xml(node, self.runtime_mock, self.keys, self.id_gen_mock)
        try:
            self.assertEqual(block.discussion_id, id_pair.value)
            self.assertEqual(block.discussion_category, category_pair.value)
            self.assertEqual(block.discussion_target, target_pair.value)
        except AssertionError:
            print xblock_xml
            raise

    @mock.patch(DISCUSSION_XBLOCK_LOCATION + ".load_definition_xml")
    @ddt.unpack
    @ddt.data(*(_make_attribute_test_cases()))
    def test_legacy_export_format(self, id_pair, category_pair, target_pair, patched_load_definition_xml):
        """
        Test that legacy export XML format can be parsed preserving field values
        """
        xblock_xml = """<discussion url_name="82bb87a2d22240b1adac2dfcc1e7e5e4"/>"""
        xblock_definition_xml = """
        <discussion
            {id_attr}="{id_value}"
            {category_attr}="{category_value}"
            {target_attr}="{target_value}"
        />""".format(
            id_attr=id_pair.name, id_value=id_pair.value,
            category_attr=category_pair.name, category_value=category_pair.value,
            target_attr=target_pair.name, target_value=target_pair.value,
        )
        node = etree.fromstring(xblock_xml)
        definition_node = etree.fromstring(xblock_definition_xml)

        patched_load_definition_xml.return_value = (definition_node, "irrelevant")

        block = DiscussionXBlock.parse_xml(node, self.runtime_mock, self.keys, self.id_gen_mock)
        try:
            self.assertEqual(block.discussion_id, id_pair.value)
            self.assertEqual(block.discussion_category, category_pair.value)
            self.assertEqual(block.discussion_target, target_pair.value)
        except AssertionError:
            print xblock_xml, xblock_definition_xml
            raise

    def test_export_default_discussion_id(self):
        """
        Test that default discussion_id values are not exported.

        Historically, the OLX format allowed omitting discussion ID values; in such case, the IDs are generated
        deterministically based on the course ID and the usage ID. Moreover, Studio does not allow course authors
        to edit discussion_id, so all courses authored in Studio have discussion_id omitted in OLX.

        Forcing Studio to always export discussion_id can cause data loss when switching between an older and newer
        export,  in a course with a course ID different from the one from which the export was created - because the
        discussion ID would be different.
        """
        target_node = etree.Element('dummy')

        block = DiscussionXBlock(self.runtime_mock, scope_ids=self.keys, field_data=DictFieldData({}))
        discussion_id_field = block.fields['discussion_id']

        # precondition checks - discussion_id does not have a value and uses UNIQUE_ID
        self.assertEqual(
            discussion_id_field._get_cached_value(block),  # pylint: disable=protected-access
            NO_CACHE_VALUE
        )
        self.assertEqual(discussion_id_field.default, UNIQUE_ID)

        block.add_xml_to_node(target_node)
        self.assertEqual(target_node.tag, "discussion")
        self.assertNotIn("discussion_id", target_node.attrib)

    @ddt.data("jediwannabe", "iddqd", "itisagooddaytodie")
    def test_export_custom_discussion_id(self, discussion_id):
        """
        Test that custom discussion_id values are exported
        """
        target_node = etree.Element('dummy')

        block = DiscussionXBlock(self.runtime_mock, scope_ids=self.keys, field_data=DictFieldData({}))
        block.discussion_id = discussion_id

        # precondition check
        self.assertEqual(block.discussion_id, discussion_id)

        block.add_xml_to_node(target_node)
        self.assertEqual(target_node.tag, "discussion")
        self.assertTrue(target_node.attrib["discussion_id"], discussion_id)
