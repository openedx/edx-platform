# -*- coding: utf-8 -*-
"""
Test XML parsing in XBlocks.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
import textwrap
import unittest

import ddt
from lxml import etree
import mock
import six

from xblock.core import XBlock, XML_NAMESPACES
from xblock.fields import Scope, String, Integer, Dict, List
from xblock.test.tools import blocks_are_equivalent
from xblock.test.toy_runtime import ToyRuntime

# XBlock classes to use in the tests.


def get_namespace_attrs():
    """ Returns string suitable to be used as an xmlns parameters in XBlock XML representation """
    return " ".join('xmlns:{}="{}"'.format(k, v) for k, v in six.iteritems(XML_NAMESPACES))


class Leaf(XBlock):
    """Something we can parse from XML."""
    data1 = String(default="default_value", scope=Scope.user_state)
    data2 = String(default="default_value", scope=Scope.user_state)
    content = String(default="", scope=Scope.content)


class LeafWithDictAndList(XBlock):
    """A leaf containing dict and list options."""
    dictionary = Dict(default={"default": True}, scope=Scope.user_state)
    sequence = List(default=[1, 2, 3], scope=Scope.user_state)


class LeafWithOption(Leaf):
    """A leaf with an additional option set via xml attribute."""
    data3 = Dict(
        default={}, scope=Scope.user_state, enforce_type=True,
        xml_node=True)
    data4 = List(
        default=[], scope=Scope.user_state, enforce_type=True,
        xml_node=True)


class Container(XBlock):
    """A thing with children."""
    has_children = True


class Specialized(XBlock):
    """A block that wants to do its own XML parsing."""
    num_children = Integer(default=0, scope=Scope.user_state)

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """We'll just set num_children to the number of child nodes."""
        block = runtime.construct_xblock_from_class(cls, keys)
        block.num_children = len(node)
        return block


class CustomXml(XBlock):
    """A block that does its own XML parsing and preserves comments"""
    inner_xml = String(default='', scope=Scope.content)
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """Parse the XML node and save it as a string"""
        block = runtime.construct_xblock_from_class(cls, keys)
        for child in node:
            if child.tag is not etree.Comment:
                block.runtime.add_node_as_child(block, child, id_generator)
        # Now build self.inner_xml from the XML of node's children
        # We can't just call tounicode() on each child because it adds xmlns: attributes
        xml_str = etree.tounicode(node)
        block.inner_xml = xml_str[xml_str.index('>') + 1:xml_str.rindex('<')]
        return block

    def add_xml_to_node(self, node):
        """ For exporting, set data on `node` from ourselves. """
        node.tag = self.xml_element_name()
        parsed_inner_xml = etree.XML('<x>{}</x>'.format(self.inner_xml))
        node.text = parsed_inner_xml.text
        for child in parsed_inner_xml:
            node.append(child)

# Helpers


class XmlTestMixin(object):
    """
    Wraps parsing and exporting and other things to return more useful values. Does not define
    a runtime (thus calling it a mixin)
    """
    def parse_xml_to_block(self, xml):
        """A helper to get a block from some XML."""
        usage_id = self.runtime.parse_xml_string(xml)
        block = self.runtime.get_block(usage_id)
        return block

    def export_xml_for_block(self, block):
        """A helper to return the XML string for a block."""
        output = six.BytesIO()
        self.runtime.export_to_xml(block, output)
        return output.getvalue()


class XmlTest(XmlTestMixin, unittest.TestCase):
    """Helpful things for XML tests."""
    def setUp(self):
        super(XmlTest, self).setUp()
        self.runtime = ToyRuntime()


# Tests!

class ParsingTest(XmlTest, unittest.TestCase):
    """Tests of XML parsing."""

    @XBlock.register_temp_plugin(Leaf)
    def test_parsing(self):
        block = self.parse_xml_to_block("<leaf data2='parsed'/>")

        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.data1, "default_value")
        self.assertEqual(block.data2, "parsed")
        self.assertEqual(block.content, "")

    @XBlock.register_temp_plugin(Leaf)
    def test_parsing_content(self):
        block = self.parse_xml_to_block("<leaf>my text!</leaf>")

        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.content, "my text!")

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Container)
    def test_parsing_children(self):
        block = self.parse_xml_to_block("""\
                    <container>
                        <leaf data1='child1'/>
                        <leaf data1='child2'/>
                    </container>
                    """)
        self.assertIsInstance(block, Container)
        self.assertEqual(len(block.children), 2)

        child1 = self.runtime.get_block(block.children[0])
        self.assertIsInstance(child1, Leaf)
        self.assertEqual(child1.data1, "child1")
        self.assertEqual(child1.parent, block.scope_ids.usage_id)

        child2 = self.runtime.get_block(block.children[1])
        self.assertIsInstance(child2, Leaf)
        self.assertEqual(child2.data1, "child2")
        self.assertEqual(child2.parent, block.scope_ids.usage_id)

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Container)
    def test_xml_with_comments(self):
        block = self.parse_xml_to_block("""\
                    <!-- This is a comment -->
                    <container>
                        <leaf data1='child1'/>
                        <!-- <leaf data1='ignore'/> -->
                        <leaf data1='child2'/>
                    </container>
                    """)
        self.assertIsInstance(block, Container)
        self.assertEqual(len(block.children), 2)

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(CustomXml)
    def test_comments_in_field_preserved(self):
        """
        Check that comments made by users inside field data are preserved.
        """
        block = self.parse_xml_to_block("""\
                    <!-- This is a comment outside a block - it can be lost -->
                    <customxml>A<!--B--><leaf/>C<leaf/><!--D-->E</customxml>
                    """)
        self.assertIsInstance(block, CustomXml)
        self.assertEqual(len(block.children), 2)

        xml = self.export_xml_for_block(block)
        self.assertIn(b'A<!--B--><leaf/>C<leaf/><!--D-->E', xml)
        block_imported = self.parse_xml_to_block(xml)
        self.assertEqual(
            block_imported.inner_xml,
            'A<!--B--><leaf/>C<leaf/><!--D-->E',
        )

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Specialized)
    def test_customized_parsing(self):
        block = self.parse_xml_to_block("""\
                    <specialized>
                        <leaf/><leaf/><leaf/>
                    </specialized>
                    """)
        self.assertIsInstance(block, Specialized)
        self.assertEqual(block.num_children, 3)

    @XBlock.register_temp_plugin(Leaf)
    def test_parse_unicode(self):
        block = self.parse_xml_to_block("<leaf data1='\u2603' />")
        self.assertIsInstance(block, Leaf)
        self.assertEqual(block.data1, '\u2603')


@ddt.ddt
class ExportTest(XmlTest, unittest.TestCase):
    """Tests of the XML export facility."""

    @XBlock.register_temp_plugin(Leaf)
    def test_dead_simple_export(self):
        block = self.parse_xml_to_block("<leaf/>")
        xml = self.export_xml_for_block(block)
        self.assertIn(
            b"<?xml version='1.0' encoding='UTF-8'?>\n<leaf ",
            xml,
        )

    @XBlock.register_temp_plugin(Leaf)
    def test_dead_simple_export_binary(self):
        block = self.parse_xml_to_block(b"<leaf/>")
        xml = self.export_xml_for_block(block)
        self.assertIn(
            b"<?xml version='1.0' encoding='UTF-8'?>\n<leaf ",
            xml,
        )

    @XBlock.register_temp_plugin(Leaf)
    @XBlock.register_temp_plugin(Container)
    def test_export_then_import(self):
        block_body = """\
            <?xml version='1.0' encoding='utf-8'?>
            <container>
                <leaf data1='child1' data2='I&#39;m also child1' />
                <leaf data2="me too!" data1='child2' ></leaf>
                <container>
                    <leaf data1='ʇxǝʇ uʍop-ǝpısdn' data2='whoa'>
                        ᵾnɨȼøđɇ ȼȺn ƀɇ ŧɍɨȼꝁɏ!
                    </leaf>
                </container>
                <leaf>Some text content.</leaf>
            </container>
            """
        block = self.parse_xml_to_block(textwrap.dedent(block_body).encode('utf-8'))
        xml = self.export_xml_for_block(block)
        block_imported = self.parse_xml_to_block(xml)

        # Crude checks that the XML is correct.  The exact form of the XML
        # isn't important.
        xml = xml.decode('utf-8')
        self.assertEqual(xml.count("container"), 4)
        self.assertEqual(xml.count("child1"), 2)
        self.assertEqual(xml.count("child2"), 1)
        self.assertEqual(xml.count("ʇxǝʇ uʍop-ǝpısdn"), 1)
        self.assertEqual(xml.count("ᵾnɨȼøđɇ ȼȺn ƀɇ ŧɍɨȼꝁɏ!"), 1)

        # The important part: exporting then importing a block should give
        # you an equivalent block.
        self.assertTrue(blocks_are_equivalent(block, block_imported))

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_dict_and_list_as_attribute(self):
        block = self.parse_xml_to_block(textwrap.dedent("""\
            <?xml version='1.0' encoding='utf-8'?>
            <leafwithdictandlist
                dictionary='{"foo": "bar"}'
                sequence='["one", "two", "three"]' />
            """).encode('utf-8'))

        self.assertEqual(block.dictionary, {"foo": "bar"})
        self.assertEqual(block.sequence, ["one", "two", "three"])

    @XBlock.register_temp_plugin(LeafWithOption)
    def test_export_then_import_with_options(self):
        block = self.parse_xml_to_block(textwrap.dedent("""\
            <?xml version='1.0' encoding='utf-8'?>
            <leafwithoption xmlns:option="http://code.edx.org/xblock/option"
                data1="child1" data2='with a dict'>
                <option:data3>
                    child: 1
                    with custom option: True
                </option:data3>
                <option:data4>
                    - 1.23
                    - true
                    - some string
                </option:data4>
            </leafwithoption>
            """).encode('utf-8'))
        xml = self.export_xml_for_block(block)

        block_imported = self.parse_xml_to_block(xml)

        self.assertEqual(block_imported.data3, {"child": 1, "with custom option": True})
        self.assertEqual(block_imported.data4, [1.23, True, "some string"])

        self.assertEqual(xml.count(b"child1"), 1)
        self.assertTrue(blocks_are_equivalent(block, block_imported))

    @XBlock.register_temp_plugin(LeafWithOption)
    def test_dict_and_list_export_format(self):
        xml = textwrap.dedent("""\
            <?xml version='1.0' encoding='UTF-8'?>
            <leafwithoption %s xblock-family="xblock.v1">
              <option:data4>[
              1.23,
              true,
              "some string"
            ]</option:data4>
              <option:data3>{
              "child": 1,
              "with custom option": true
            }</option:data3>
            </leafwithoption>
            """) % get_namespace_attrs()
        block = self.parse_xml_to_block(xml.encode('utf-8'))
        exported_xml = self.export_xml_for_block(block)
        self.assertIn(
            '<option:data4>[\n  1.23,\n  true,\n  "some string"\n]</option:data4>\n',
            exported_xml.decode('utf-8')
        )
        self.assertIn(
            '<option:data3>{\n  "child": 1,\n  "with custom option": true\n}</option:data3>\n',
            exported_xml.decode('utf-8')
        )

    @XBlock.register_temp_plugin(Leaf)
    @ddt.data(
        "apoapsis",
        "periapsis",
        "inclination",
        "eccentricity"
    )
    def test_unknown_field_as_attribute_raises_warning(self, parameter_name):
        with mock.patch('logging.warning') as patched_warn:
            block = self.parse_xml_to_block("<leaf {0}='something irrelevant'></leaf>".format(parameter_name))
            patched_warn.assert_called_once_with("XBlock %s does not contain field %s", type(block), parameter_name)

    @XBlock.register_temp_plugin(LeafWithOption)
    @ddt.data(
        "apoapsis",
        "periapsis",
        "inclination",
        "eccentricity"
    )
    def test_unknown_field_as_node_raises_warning(self, parameter_name):
        xml = textwrap.dedent("""\
            <leafwithoption %s>
                <option:%s>Some completely irrelevant data</option:%s>
            </leafwithoption>
        """) % (get_namespace_attrs(), parameter_name, parameter_name)
        with mock.patch('logging.warning') as patched_warn:
            block = self.parse_xml_to_block(xml)
            patched_warn.assert_called_once_with("XBlock %s does not contain field %s", type(block), parameter_name)


class TestRoundTrip(XmlTest, unittest.TestCase):
    """ Test serialization-deserialization sequence """

    def create_block(self, block_type):
        """
        Create a block
        """
        def_id = self.runtime.id_generator.create_definition(block_type)
        usage_id = self.runtime.id_generator.create_usage(def_id)
        block = self.runtime.get_block(usage_id)
        return block

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_string_roundtrip(self):
        """
        Test correctly serializes-deserializes List and Dicts with byte string
        contents in Python 2.

        In Python 3, this behavior is unsupported.  dict and list elements
        cannot be bytes objects.
        """
        block = self.create_block("leafwithdictandlist")

        expected_seq = [b'1', b'2']
        expected_dict = {b'1': b'1', b'ping': b'ack'}
        block.sequence = expected_seq
        block.dictionary = expected_dict
        if six.PY3:
            self.assertRaises(TypeError, self.export_xml_for_block, block)
        else:
            xml = self.export_xml_for_block(block)
            parsed = self.parse_xml_to_block(xml)

            self.assertEqual(parsed.sequence, expected_seq)
            self.assertEqual(parsed.dictionary, expected_dict)

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_unicode_roundtrip(self):
        """ Test correctly serializes-deserializes List and Dicts with unicode contents """
        block = self.create_block("leafwithdictandlist")

        expected_seq = ['1', '2']
        expected_dict = {'1': '1', 'ping': 'ack'}
        block.sequence = expected_seq
        block.dictionary = expected_dict
        xml = self.export_xml_for_block(block)

        parsed = self.parse_xml_to_block(xml)

        self.assertEqual(parsed.sequence, expected_seq)
        self.assertEqual(parsed.dictionary, expected_dict)

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_integers_roundtrip(self):
        """ Test correctly serializes-deserializes List and Dicts with integer contents """
        block = self.create_block("leafwithdictandlist")

        expected_seq = [1, 2, 3]
        expected_dict = {1: 10, 2: 20}
        block.sequence = expected_seq
        block.dictionary = expected_dict
        xml = self.export_xml_for_block(block)
        parsed = self.parse_xml_to_block(xml)

        self.assertEqual(parsed.sequence, expected_seq)
        self.assertNotEqual(parsed.dictionary, expected_dict)
        self.assertEqual(parsed.dictionary, {six.text_type(key): value for key, value in six.iteritems(expected_dict)})

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_none_contents_roundtrip(self):
        """ Test correctly serializes-deserializes List and Dicts with keys/values of None """
        block = self.create_block("leafwithdictandlist")

        expected_seq = [1, None, 3, None]
        expected_dict = {"1": None, None: 20}
        block.sequence = expected_seq
        block.dictionary = expected_dict
        xml = self.export_xml_for_block(block)
        parsed = self.parse_xml_to_block(xml)

        self.assertEqual(parsed.sequence, expected_seq)
        self.assertNotEqual(parsed.dictionary, expected_dict)
        self.assertEqual(parsed.dictionary, {"1": None, 'null': 20})

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_none_roundtrip(self):
        """ Test correctly serializes-deserializes Null List and Dict fields """
        block = self.create_block("leafwithdictandlist")

        block.sequence = None
        block.dictionary = None
        xml = self.export_xml_for_block(block)
        parsed = self.parse_xml_to_block(xml)

        self.assertIsNone(parsed.sequence)
        self.assertIsNone(parsed.dictionary)

    @XBlock.register_temp_plugin(LeafWithDictAndList)
    def test_nested_roundtrip(self):
        """ Test correctly serializes-deserializes nested List and Dict fields """
        block = self.create_block("leafwithdictandlist")

        expected_seq = [[1, 2], ["3", "4"], {"1": "2"}]
        expected_dict = {"outer1": {"inner1": "1", "inner2": 2}, "outer2": [1, 2, 3]}
        block.sequence = expected_seq
        block.dictionary = expected_dict
        xml = self.export_xml_for_block(block)
        parsed = self.parse_xml_to_block(xml)

        self.assertEqual(parsed.sequence, expected_seq)
        self.assertEqual(parsed.dictionary, expected_dict)


def squish(text):
    """Turn any run of whitespace into one space."""
    return re.sub(r"\s+", " ", text)
