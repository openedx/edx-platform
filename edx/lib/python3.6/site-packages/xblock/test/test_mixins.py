"""
Tests of the XBlock-family functionality mixins
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime
from unittest import TestCase

import ddt as ddt
from lxml import etree
import mock
import pytz
import six

from xblock.core import XBlock, XBlockAside
from xblock.fields import List, Scope, Integer, String, ScopeIds, UNIQUE_ID, DateTime
from xblock.field_data import DictFieldData
from xblock.mixins import ScopedStorageMixin, HierarchyMixin, IndexInfoMixin, ViewsMixin, XML_NAMESPACES
from xblock.runtime import Runtime


class AttrAssertionMixin(TestCase):
    """
    A mixin to add attribute assertion methods to TestCases.
    """
    def assertHasAttr(self, obj, attr):
        "Assert that `obj` has the attribute named `attr`."
        self.assertTrue(hasattr(obj, attr), "{!r} doesn't have attribute {!r}".format(obj, attr))

    def assertNotHasAttr(self, obj, attr):
        "Assert that `obj` doesn't have the attribute named `attr`."
        self.assertFalse(hasattr(obj, attr), "{!r} has attribute {!r}".format(obj, attr))


class TestScopedStorageMixin(AttrAssertionMixin, TestCase):
    "Tests of the ScopedStorageMixin."

    class ScopedStorageMixinTester(ScopedStorageMixin):
        """Toy class for ScopedStorageMixin testing"""

        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content)

    class ChildClass(ScopedStorageMixinTester):
        """Toy class for ModelMetaclass testing"""
        pass

    class FieldsMixin(object):
        """Toy mixin for field testing"""
        field_c = Integer(scope=Scope.settings)

    class MixinChildClass(FieldsMixin, ScopedStorageMixinTester):
        """Toy class for ScopedStorageMixin testing with mixed-in fields"""
        pass

    class MixinGrandchildClass(MixinChildClass):
        """Toy class for ScopedStorageMixin testing with inherited mixed-in fields"""
        pass

    def test_scoped_storage_mixin(self):

        # `ModelMetaclassTester` and `ChildClass` both obtain the `fields` attribute
        # from the `ModelMetaclass`. Since this is not understood by static analysis,
        # silence this error for the duration of this test.
        # pylint: disable=E1101
        self.assertIsNot(self.ScopedStorageMixinTester.fields, self.ChildClass.fields)

        self.assertHasAttr(self.ScopedStorageMixinTester, 'field_a')
        self.assertHasAttr(self.ScopedStorageMixinTester, 'field_b')

        self.assertIs(self.ScopedStorageMixinTester.field_a, self.ScopedStorageMixinTester.fields['field_a'])
        self.assertIs(self.ScopedStorageMixinTester.field_b, self.ScopedStorageMixinTester.fields['field_b'])

        self.assertHasAttr(self.ChildClass, 'field_a')
        self.assertHasAttr(self.ChildClass, 'field_b')

        self.assertIs(self.ChildClass.field_a, self.ChildClass.fields['field_a'])
        self.assertIs(self.ChildClass.field_b, self.ChildClass.fields['field_b'])

    def test_with_mixins(self):
        # Testing model metaclass with mixins

        # `MixinChildClass` and `MixinGrandchildClass` both obtain the `fields` attribute
        # from the `ScopedStorageMixin`. Since this is not understood by static analysis,
        # silence this error for the duration of this test.
        # pylint: disable=E1101

        self.assertHasAttr(self.MixinChildClass, 'field_a')
        self.assertHasAttr(self.MixinChildClass, 'field_c')
        self.assertIs(self.MixinChildClass.field_a, self.MixinChildClass.fields['field_a'])
        self.assertIs(self.FieldsMixin.field_c, self.MixinChildClass.fields['field_c'])

        self.assertHasAttr(self.MixinGrandchildClass, 'field_a')
        self.assertHasAttr(self.MixinGrandchildClass, 'field_c')
        self.assertIs(self.MixinGrandchildClass.field_a, self.MixinGrandchildClass.fields['field_a'])
        self.assertIs(self.MixinGrandchildClass.field_c, self.MixinGrandchildClass.fields['field_c'])


class TestHierarchyMixin(AttrAssertionMixin, TestCase):
    "Tests of the HierarchyMixin."

    class HasChildren(HierarchyMixin):
        """Toy class for ChildrenModelMetaclass testing"""
        has_children = True

    class WithoutChildren(HierarchyMixin):
        """Toy class for ChildrenModelMetaclass testing"""
        pass

    class InheritedChildren(HasChildren):
        """Toy class for ChildrenModelMetaclass testing"""
        pass

    def test_children_metaclass(self):
        # `HasChildren` and `WithoutChildren` both obtain the `children` attribute and
        # the `has_children` method from the `ChildrenModelMetaclass`. Since this is not
        # understood by static analysis, silence this error for the duration of this test.
        # pylint: disable=E1101

        self.assertTrue(self.HasChildren.has_children)
        self.assertFalse(self.WithoutChildren.has_children)
        self.assertTrue(self.InheritedChildren.has_children)

        self.assertHasAttr(self.HasChildren, 'children')
        self.assertNotHasAttr(self.WithoutChildren, 'children')
        self.assertHasAttr(self.InheritedChildren, 'children')

        self.assertIsInstance(self.HasChildren.children, List)
        self.assertEqual(Scope.children, self.HasChildren.children.scope)
        self.assertIsInstance(self.InheritedChildren.children, List)
        self.assertEqual(Scope.children, self.InheritedChildren.children.scope)


class TestIndexInfoMixin(AttrAssertionMixin):
    """
    Tests for Index
    """
    class IndexInfoMixinTester(IndexInfoMixin):
        """Test class for index mixin"""
        pass

    def test_index_info(self):
        self.assertHasAttr(self.IndexInfoMixinTester, 'index_dictionary')
        with_index_info = self.IndexInfoMixinTester().index_dictionary()
        self.assertFalse(with_index_info)
        self.assertTrue(isinstance(with_index_info, dict))


class TestViewsMixin(TestCase):
    """
    Tests for ViewsMixin
    """
    def test_supports_view_decorator(self):
        """
        Tests the @supports decorator for xBlock view methods
        """
        class SupportsDecoratorTester(ViewsMixin):
            """
            Test class for @supports decorator
            """
            @ViewsMixin.supports("a_functionality")
            def functionality_supported_view(self):
                """
                A view that supports a functionality
                """
                pass  # pragma: no cover

            @ViewsMixin.supports("functionality1", "functionality2")
            def multi_featured_view(self):
                """
                A view that supports multiple functionalities
                """
                pass  # pragma: no cover

            def an_unsupported_view(self):
                """
                A view that does not support any functionality
                """
                pass  # pragma: no cover

        test_xblock = SupportsDecoratorTester()

        for view_name, functionality, expected_result in (
                ("functionality_supported_view", "a_functionality", True),
                ("functionality_supported_view", "bogus_functionality", False),
                ("functionality_supported_view", None, False),

                ("an_unsupported_view", "a_functionality", False),

                ("multi_featured_view", "functionality1", True),
                ("multi_featured_view", "functionality2", True),
                ("multi_featured_view", "bogus_functionality", False),
        ):
            self.assertEqual(
                test_xblock.has_support(getattr(test_xblock, view_name), functionality),
                expected_result
            )

    def test_has_support_override(self):
        """
        Tests overriding has_support
        """
        class HasSupportOverrideTester(ViewsMixin):
            """
            Test class for overriding has_support
            """
            def has_support(self, view, functionality):
                """
                Overrides implementation of has_support
                """
                return functionality == "a_functionality"

        test_xblock = HasSupportOverrideTester()

        for view_name, functionality, expected_result in (
                ("functionality_supported_view", "a_functionality", True),
                ("functionality_supported_view", "bogus_functionality", False),
        ):
            self.assertEqual(
                test_xblock.has_support(getattr(test_xblock, view_name, None), functionality),
                expected_result
            )


@ddt.ddt
class TestXmlSerializationMixin(TestCase):
    """ Tests for XmlSerialization Mixin """

    # pylint:disable=invalid-name
    class TestXBlock(XBlock):
        """ XBlock for XML export test """
        etree_node_tag = 'test_xblock'

        str_field = String()
        str_str_default = String(default="default")
        str_str_default_force_export = String(default="default", force_export=True)
        str_uid_default = String(default=UNIQUE_ID)
        str_uid_default_force_export = String(default=UNIQUE_ID, force_export=True)
        str_none_default = String(default=None)
        str_none_default_force_export = String(default=None, force_export=True)

    # pylint:disable=invalid-name
    class TestXBlockAside(XBlockAside):
        """ XBlockAside for XML export test """
        etree_node_tag = 'test_xblock_aside'

        str_field = String()
        str_str_default = String(default="default")

    class TestXBlockWithDateTime(XBlock):
        """ XBlock for DateTime fields export """
        etree_node_tag = 'test_xblock_with_datetime'

        datetime = DateTime(default=None)

    def setUp(self):
        """
        Construct test XBlocks.
        """
        self.test_xblock = self._make_block(self.TestXBlock)
        self.test_xblock_tag = self.TestXBlock.etree_node_tag
        self.test_xblock_datetime = self._make_block(self.TestXBlockWithDateTime)
        self.test_xblock_datetime_tag = self.TestXBlockWithDateTime.etree_node_tag
        self.test_xblock_aside = self._make_block(self.TestXBlockAside)
        self.test_xblock_aside_tag = self.TestXBlockAside.etree_node_tag

    def _make_block(self, block_type=None):
        """ Creates a test block """
        block_type = block_type if block_type else self.TestXBlock
        runtime_mock = mock.Mock(spec=Runtime)
        scope_ids = ScopeIds("user_id", block_type.etree_node_tag, "def_id", "usage_id")
        return block_type(runtime=runtime_mock, field_data=DictFieldData({}), scope_ids=scope_ids)

    def _assert_node_attributes(self, node, expected_attributes, entry_point=None):
        """ Checks XML node attributes to match expected_attributes"""
        node_attributes = list(node.keys())
        node_attributes.remove('xblock-family')

        self.assertEqual(node.get('xblock-family'), entry_point if entry_point else self.TestXBlock.entry_point)
        self.assertEqual(set(node_attributes), set(expected_attributes.keys()))

        for key, value in six.iteritems(expected_attributes):
            if value != UNIQUE_ID:
                self.assertEqual(node.get(key), value)
            else:
                self.assertIsNotNone(node.get(key))

    def _assert_node_elements(self, node, expected_elements):
        """
        Checks XML node elements to match expected elements.
        """
        node_elements = list(node)
        self.assertEqual(set([elem.tag for elem in node_elements]), set(expected_elements.keys()))
        # All elements on the node are expected to have a "none"="true" attribute.
        for elem in node:
            self.assertEqual(elem.get('none'), 'true')

    def test_no_fields_set_add_xml_to_node(self):
        """
        Tests that no fields are set on a TestXBlock when initially made
        and no fields are present in the XML (besides force-exported defaults).
        """
        node = etree.Element(self.test_xblock_tag)

        # Precondition check: no fields are set.
        for field_name in six.iterkeys(self.test_xblock.fields):
            self.assertFalse(self.test_xblock.fields[field_name].is_set_on(self.test_xblock))

        self.test_xblock.add_xml_to_node(node)

        self._assert_node_attributes(
            node,
            {
                'str_str_default_force_export': 'default',
                'str_uid_default_force_export': UNIQUE_ID
            }
        )
        self._assert_node_elements(
            node,
            {
                # The tag is prefixed with {namespace}.
                '{{{}}}{}'.format(
                    XML_NAMESPACES["option"],
                    'str_none_default_force_export'
                ): None
            }
        )

    def test_set_fields_add_xml_to_node(self):
        """
        Tests that set fields appear in XML after add_xml_to_node.
        """
        node = etree.Element(self.test_xblock_tag)

        self.test_xblock.str_field = 'str_field_val'
        self.test_xblock.str_str_default = 'str_str_default_val'
        self.test_xblock.str_str_default_force_export = 'str_str_default_force_export_val'
        self.test_xblock.str_uid_default = 'str_uid_default_val'
        self.test_xblock.str_uid_default_force_export = 'str_uid_default_force_export_val'
        self.test_xblock.str_none_default = 'str_none_default_val'
        self.test_xblock.str_none_default_force_export = 'str_none_default_force_export_val'

        self.test_xblock.add_xml_to_node(node)

        self._assert_node_attributes(
            node,
            {
                'str_field': 'str_field_val',
                'str_str_default': 'str_str_default_val',
                'str_str_default_force_export': 'str_str_default_force_export_val',
                'str_uid_default': 'str_uid_default_val',
                'str_uid_default_force_export': 'str_uid_default_force_export_val',
                'str_none_default': 'str_none_default_val',
                'str_none_default_force_export': 'str_none_default_force_export_val',
            }
        )
        self._assert_node_elements(node, {})

    def test_set_field_to_none_add_xml_to_node(self):
        """
        Tests add_xml_to_node with String field value set to None.
        """
        node = etree.Element(self.test_xblock_tag)

        # Now set all fields to None.
        self.test_xblock.str_field = None
        self.test_xblock.str_str_default = None
        self.test_xblock.str_str_default_force_export = None
        self.test_xblock.str_uid_default = None
        self.test_xblock.str_uid_default_force_export = None
        self.test_xblock.str_none_default = None
        self.test_xblock.str_none_default_force_export = None

        self.test_xblock.add_xml_to_node(node)

        self._assert_node_attributes(node, {})
        self._assert_node_elements(
            node,
            {
                # The tags are prefixed with {namespace}.
                '{{{}}}{}'.format(XML_NAMESPACES["option"], tag): None
                for tag in [
                    'str_field',
                    'str_str_default',
                    'str_str_default_force_export',
                    'str_uid_default',
                    'str_uid_default_force_export',
                    'str_none_default',
                    'str_none_default_force_export'
                ]
            }
        )

    def test_set_unset_then_add_xml_to_node(self):
        """
        Tests add_xml_to_node with non-UNIQUE_ID String field value unset after being set.
        """
        node = etree.Element(self.test_xblock_tag)

        # Now set some fields to values.
        self.test_xblock.str_field = None
        self.test_xblock.str_str_default = 'water is wet'
        self.test_xblock.str_str_default_force_export = ''
        self.test_xblock.str_uid_default = 'smart'
        self.test_xblock.str_uid_default_force_export = '47'
        self.test_xblock.str_none_default = ''
        self.test_xblock.str_none_default_force_export = None

        # Now unset those same fields.
        del self.test_xblock.str_field
        del self.test_xblock.str_str_default
        del self.test_xblock.str_str_default_force_export
        del self.test_xblock.str_uid_default
        del self.test_xblock.str_uid_default_force_export
        del self.test_xblock.str_none_default
        del self.test_xblock.str_none_default_force_export

        self.test_xblock.add_xml_to_node(node)

        # The fields should no longer be present in the XML representation.
        self._assert_node_attributes(
            node,
            {
                'str_str_default_force_export': 'default',
                'str_uid_default_force_export': UNIQUE_ID
            }
        )
        self._assert_node_elements(
            node,
            {
                # The tag is prefixed with {namespace}.
                '{{{}}}{}'.format(
                    XML_NAMESPACES["option"],
                    'str_none_default_force_export'
                ): None
            }
        )

    def test_xblock_aside_add_xml_to_node(self):
        """
        Tests that add_xml_to_node works proper for xblock aside.
        """
        node = etree.Element(self.test_xblock_aside_tag)

        self.test_xblock_aside.str_field = 'str_field_val_aside'
        self.test_xblock_aside.str_str_default = 'str_str_default_val'
        self.test_xblock_aside.add_xml_to_node(node)

        self._assert_node_attributes(
            node,
            {
                'str_field': 'str_field_val_aside',
                'str_str_default': 'str_str_default_val',
            },
            self.TestXBlockAside.entry_point
        )
        self._assert_node_elements(node, {})

    @ddt.data(
        (None, {'datetime': ''}),
        (datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc), {'datetime': '2014-04-01T02:03:04.567890'})
    )
    @ddt.unpack
    def test_datetime_serialization(self, value, expected_attributes):
        """
        Tests exporting DateTime fields to XML
        """
        node = etree.Element(self.test_xblock_datetime_tag)

        self.test_xblock_datetime.datetime = value

        self.test_xblock_datetime.add_xml_to_node(node)

        self._assert_node_attributes(node, expected_attributes)
