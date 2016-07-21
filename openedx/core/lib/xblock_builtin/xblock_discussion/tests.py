""" Tests for DiscussionXBLock"""
import ddt
import mock
from nose.plugins.attrib import attr
from unittest import TestCase

from safe_lxml import etree

from openedx.core.lib.xblock_builtin.xblock_discussion.xblock_discussion import DiscussionXBlock
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds, UNIQUE_ID, NO_CACHE_VALUE
from xblock.runtime import Runtime


@attr('shard2')
@ddt.ddt
class DiscussionXBlockImportExportTests(TestCase):
    """
    Import and export tests
    """
    DISCUSSION_XBLOCK_LOCATION = "openedx.core.lib.xblock_builtin.xblock_discussion.xblock_discussion.DiscussionXBlock"

    @staticmethod
    def _make_xml_node(xml_string):
        """
        Builds etree Element from string XML
        """
        return etree.fromstring(xml_string)

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

    def _construct_xblock_mock(self, cls, keys):
        """
        Builds target xblock instance (DiscussionXBlock)

        Signature-compatible with runtime.construct_xblock_from_class - can be used as a mock side-effect
        """
        return DiscussionXBlock(self.runtime_mock, scope_ids=keys, field_data=DictFieldData({}))

    @mock.patch(DISCUSSION_XBLOCK_LOCATION + ".load_definition_xml")
    @ddt.unpack
    @ddt.data(
        ("ID1", "Test category", "Test target"),
        ("ID2", "Some other category", "Some other target")
    )
    def test_xblock_export_format(self, discussion_id, category, target, patched_load_definition_xml):
        """
        Test that xblock export XML format can be parsed preserving field values
        """
        xblock_xml = """
        <discussion
            url_name="82bb87a2d22240b1adac2dfcc1e7e5e4" xblock-family="xblock.v1"
            discussion_id="{discussion_id}"
            discussion_category="{category}"
            discussion_target="{target}"
        />
        """.format(discussion_id=discussion_id, category=category, target=target)
        node = self._make_xml_node(xblock_xml)

        patched_load_definition_xml.side_effect = Exception("Irrelevant")

        block = DiscussionXBlock.parse_xml(node, self.runtime_mock, self.keys, self.id_gen_mock)
        self.assertEqual(block.discussion_id, discussion_id)
        self.assertEqual(block.discussion_category, category)
        self.assertEqual(block.discussion_target, target)

    @mock.patch(DISCUSSION_XBLOCK_LOCATION + ".load_definition_xml")
    @ddt.unpack
    @ddt.data(
        ("ID1", "Test category", "Test target"),
        ("ID2", "Some other category", "Some other target")
    )
    def test_legacy_export_format(self, discussion_id, category, target, patched_load_definition_xml):
        """
        Test that legacy export XML format can be parsed preserving field values
        """
        xblock_xml = """
            <discussion url_name="82bb87a2d22240b1adac2dfcc1e7e5e4" discussion_id="{discussion_id}"/>
        """.format(discussion_id=discussion_id)
        xblock_definition_xml = """
            <discussion discussion_category="{category}" discussion_target="{target}"/>
        """.format(category=category, target=target)
        node = self._make_xml_node(xblock_xml)
        definition_node = self._make_xml_node(xblock_definition_xml)

        patched_load_definition_xml.return_value = (definition_node, "irrelevant")

        block = DiscussionXBlock.parse_xml(node, self.runtime_mock, self.keys, self.id_gen_mock)
        self.assertEqual(block.discussion_category, category)
        self.assertEqual(block.discussion_target, target)

    def test_export_default_discussion_id(self):
        """
        Test that default discussion_id values are not exported
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
