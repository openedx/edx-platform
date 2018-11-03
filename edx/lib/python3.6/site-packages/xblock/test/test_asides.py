"""
Test XBlock Aside
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import six

from web_fragments.fragment import Fragment

from xblock.core import XBlockAside, XBlock
from xblock.fields import ScopeIds, Scope, String
from xblock.runtime import DictKeyValueStore, KvsFieldData
from xblock.test.test_runtime import TestXBlock
from xblock.test.tools import TestRuntime
from xblock.test.test_parsing import Leaf, XmlTestMixin


class TestAside(XBlockAside):
    """
    Test xblock aside class
    """
    __test__ = False
    FRAG_CONTENT = "<p>Aside rendered</p>"

    content = String(default="default_value", scope=Scope.content)
    data2 = String(default="default_value", scope=Scope.user_state)

    @XBlockAside.aside_for('student_view')
    def student_view_aside(self, block, context):  # pylint: disable=unused-argument
        """Add to the student view"""
        return Fragment(self.FRAG_CONTENT)

    @XBlockAside.aside_for('studio_view')
    def studio_view_aside(self, block, context):  # pylint: disable=unused-argument
        """Add to the studio view"""
        return Fragment(self.FRAG_CONTENT)

    @classmethod
    def should_apply_to_block(cls, block):
        """Overrides base implementation for testing purposes"""
        return block.content != 'should not apply'


class TestInheritedAside(TestAside):
    """
    XBlock Aside that inherits an aside view function from its parent.
    """
    FRAG_CONTENT = "<p>Inherited aside rendered</p>"


class AsideRuntimeSetup(TestCase):
    """
    A base class to setup the runtime
    """
    def setUp(self):
        key_store = DictKeyValueStore()
        field_data = KvsFieldData(key_store)
        self.runtime = TestRuntime(services={'field-data': field_data})


class TestAsides(AsideRuntimeSetup):
    """
    Tests of XBlockAsides.
    """
    def setUp(self):
        super(TestAsides, self).setUp()
        block_type = 'test_aside'
        def_id = self.runtime.id_generator.create_definition(block_type)
        usage_id = self.runtime.id_generator.create_usage(def_id)
        self.tester = TestXBlock(self.runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))

    @XBlockAside.register_temp_plugin(TestAside)
    def test_render_aside(self):
        """
        Test that rendering the xblock renders its aside
        """
        frag = self.runtime.render(self.tester, 'student_view', ["ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'author_view', ["ignore"])
        self.assertNotIn(TestAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'studio_view', ["ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())

    @XBlockAside.register_temp_plugin(TestAside)
    @XBlockAside.register_temp_plugin(TestInheritedAside)
    def test_inherited_aside_view(self):
        """
        Test that rendering the xblock renders its aside (when the aside view is
        inherited).
        """
        frag = self.runtime.render(self.tester, 'student_view', ["ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())
        self.assertIn(TestInheritedAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'author_view', ["ignore"])
        self.assertNotIn(TestAside.FRAG_CONTENT, frag.body_html())
        self.assertNotIn(TestInheritedAside.FRAG_CONTENT, frag.body_html())

        frag = self.runtime.render(self.tester, 'studio_view', ["ignore"])
        self.assertIn(TestAside.FRAG_CONTENT, frag.body_html())
        self.assertIn(TestInheritedAside.FRAG_CONTENT, frag.body_html())

    @XBlockAside.register_temp_plugin(TestAside)
    def test_aside_should_apply_to_block(self):
        """
        Test that should_apply_to_block returns True by default, and that it prevents
        the aside from being applied to the given block when it returns False.
        """
        self.assertTrue(TestAside.should_apply_to_block(self.tester))
        test_aside_instances = [
            inst for inst in self.runtime.get_asides(self.tester) if isinstance(inst, TestAside)
        ]
        self.assertEqual(len(test_aside_instances), 1)

        self.tester.content = 'should not apply'
        self.assertFalse(TestAside.should_apply_to_block(self.tester))
        test_aside_instances = [
            instance for instance in self.runtime.get_asides(self.tester) if isinstance(instance, TestAside)
        ]
        self.assertEqual(len(test_aside_instances), 0)


class ParsingTest(AsideRuntimeSetup, XmlTestMixin):
    """Tests of XML parsing."""
    def create_block(self):
        """
        Create a block with an aside.
        """
        block_type = 'leaf'
        def_id = self.runtime.id_generator.create_definition(block_type)
        usage_id = self.runtime.id_generator.create_usage(def_id)
        block = self.runtime.get_block(usage_id)
        block_type = 'test_aside'
        _, aside_id = self.runtime.id_generator.create_aside(def_id, usage_id, 'test_aside')
        aside = self.runtime.get_aside(aside_id)
        return block, aside

    @XBlockAside.register_temp_plugin(TestAside, 'test_aside')
    @XBlock.register_temp_plugin(Leaf)
    def test_parsing(self):
        block = self.parse_xml_to_block("""
            <leaf data2='parsed'>
                <test_aside xblock-family='xblock_asides.v1' data2='aside parsed'/>
            </leaf>
        """)

        aside = self.runtime.get_aside_of_type(block, 'test_aside')
        self.assertEqual(aside.content, "default_value")
        self.assertEqual(aside.data2, "aside parsed")

    @XBlockAside.register_temp_plugin(TestAside, 'test_aside')
    @XBlock.register_temp_plugin(Leaf)
    def test_parsing_content(self):
        block = self.parse_xml_to_block("""
            <leaf data2='parsed'>
                <test_aside xblock-family='xblock_asides.v1'>my text!</test_aside>
            </leaf>
        """)

        aside = self.runtime.get_aside_of_type(block, 'test_aside')
        self.assertEqual(aside.content, "my text!")

    def _assert_xthing_equal(self, first, second):
        """
        A quasi-equality check for xblock and xblock aside. Checks type and fields. Ignores other id and
        attrs.
        """
        self.assertEqual(first.scope_ids.block_type, second.scope_ids.block_type)
        self.assertEqual(first.fields, second.fields)
        for field in six.itervalues(first.fields):
            self.assertEqual(field.read_from(first), field.read_from(second), field)

    def _test_roundrip_of(self, block):
        """
        Serialize to and deserialize from xml then check that the result == block.
        """
        restored = self.parse_xml_to_block(self.export_xml_for_block(block))
        self._assert_xthing_equal(block, restored)
        for first, second in six.moves.zip(self.runtime.get_asides(block), self.runtime.get_asides(restored)):
            self._assert_xthing_equal(first, second)

    @XBlockAside.register_temp_plugin(TestAside, 'test_aside')
    @XBlock.register_temp_plugin(Leaf)
    def test_roundtrip(self):
        """
        Test equivalence after exporting and importing
        """
        block, aside = self.create_block()
        self._test_roundrip_of(block)
        aside.content = 'content of test aside'
        self._test_roundrip_of(block)
        aside.data2 = 'user data'
        self._test_roundrip_of(block)
