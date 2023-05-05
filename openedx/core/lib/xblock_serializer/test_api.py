"""
Test for the XBlock serialization lib's API
"""
from xml.etree import ElementTree

from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from . import api


# The expected OLX string for the 'Toy_Videos' sequential in the toy course
EXPECTED_SEQUENTIAL_OLX = """
<sequential display_name="Toy Videos" format="Lecture Sequence" url_name="Toy_Videos">
  <html url_name="secret:toylab" display_name="Toy lab"><![CDATA[
<b>Lab 2A: Superposition Experiment</b>


<p>Isn't the toy course great?</p>

<p>Let's add some markup that uses non-ascii characters.
'For example, we should be able to write words like encyclop&aelig;dia, or foreign words like fran&ccedil;ais.
Looking beyond latin-1, we should handle math symbols:  &pi;r&sup2 &le; &#8734.
And it shouldn't matter if we use entities or numeric codes &mdash; &Omega; &ne; &pi; &equiv; &#937; &#8800; &#960;.
</p>


]]></html>
  <html url_name="toyjumpto" display_name="Text"><![CDATA[
<a href="/jump_to_id/vertical_test">This is a link to another page and some Chinese 四節比分和七年前</a> <p>Some more Chinese 四節比分和七年前</p>

]]></html>
  <html url_name="toyhtml" display_name="Text"><![CDATA[
<a href='/static/handouts/sample_handout.txt'>Sample</a>
]]></html>
  <html url_name="nonportable" display_name="Text"><![CDATA[
<a href="/static/foo.jpg">link</a>

]]></html>
  <html url_name="nonportable_link" display_name="Text"><![CDATA[
<a href="/jump_to_id/nonportable_link">link</a>


]]></html>
  <html url_name="badlink" display_name="Text"><![CDATA[
<img src="/static//file.jpg" />

]]></html>
  <html url_name="with_styling" display_name="Text"><![CDATA[
<p style="font:italic bold 72px/30px Georgia, serif; color: red; ">Red text here</p>
]]></html>
  <html url_name="just_img" display_name="Text"><![CDATA[
<img src="/static/foo_bar.jpg" />
]]></html>
  <video
    display_name="Video Resources"
    url_name="Video_Resources"
    youtube="1.00:1bK-WdDi6Qw"
    youtube_id_1_0="1bK-WdDi6Qw"
  />
</sequential>
"""


@skip_unless_cms
class XBlockSerializationTestCase(SharedModuleStoreTestCase):
    """
    Test for the XBlock serialization library's python API
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a course for use in these tests
        """
        super().setUpClass()
        cls.course = ToyCourseFactory.create()

    def assertXmlEqual(self, xml_str_a: str, xml_str_b: str) -> bool:
        """ Assert that the given XML strings are equal, ignoring attribute order and some whitespace variations. """
        self.assertEqual(
            ElementTree.canonicalize(xml_str_a, strip_text=True),
            ElementTree.canonicalize(xml_str_b, strip_text=True),
        )

    def test_html_with_static_asset(self):
        """
        Test that HTML gets converted to use CDATA and static assets are
        handled.
        """
        block_id = self.course.id.make_usage_key('html', 'just_img')  # see sample_courses.py
        html_block = modulestore().get_item(block_id)
        serialized = api.serialize_xblock_to_olx(html_block)

        self.assertXmlEqual(
            serialized.olx_str,
            """
            <html display_name="Text" url_name="just_img"><![CDATA[
                <img src="/static/foo_bar.jpg" />
            ]]></html>
            """
        )
        self.assertIn("CDATA", serialized.olx_str)
        self.assertEqual(serialized.static_files, [
            api.StaticFile(
                name="foo_bar.jpg",
                url="/asset-v1:edX+toy+2012_Fall+type@asset+block@foo_bar.jpg",
                data=None,
            ),
        ])

    def test_html_with_static_asset_blockstore(self):
        """
        Test the blockstore-specific serialization of an HTML block
        """
        block_id = self.course.id.make_usage_key('html', 'just_img')  # see sample_courses.py
        html_block = modulestore().get_item(block_id)
        serialized = api.serialize_xblock_to_olx(html_block)
        serialized_blockstore = api.serialize_modulestore_block_for_blockstore(html_block)
        self.assertXmlEqual(
            serialized_blockstore.olx_str,
            # For blockstore, OLX should never contain "url_name" as that ID is specified by the filename:
            """
            <html display_name="Text"><![CDATA[
                <img src="/static/foo_bar.jpg" />
            ]]></html>
            """
        )
        self.assertIn("CDATA", serialized.olx_str)
        # Static files should be identical:
        self.assertEqual(serialized.static_files, serialized_blockstore.static_files)
        # This is the only other difference - an extra field with the blockstore-specific definition ID:
        self.assertEqual(serialized_blockstore.def_id, "html/just_img")

    def test_export_sequential(self):
        """
        Export a sequential from the toy course, including all of its children.
        """
        sequential_id = self.course.id.make_usage_key('sequential', 'Toy_Videos')  # see sample_courses.py
        sequential = modulestore().get_item(sequential_id)
        serialized = api.serialize_xblock_to_olx(sequential)

        self.assertXmlEqual(serialized.olx_str, EXPECTED_SEQUENTIAL_OLX)

    def test_export_sequential_blockstore(self):
        """
        Export a sequential from the toy course, formatted for blockstore.
        """
        sequential_id = self.course.id.make_usage_key('sequential', 'Toy_Videos')  # see sample_courses.py
        sequential = modulestore().get_item(sequential_id)
        serialized = api.serialize_modulestore_block_for_blockstore(sequential)

        self.assertXmlEqual(serialized.olx_str, """
            <sequential display_name="Toy Videos" format="Lecture Sequence">
                <xblock-include definition="html/secret:toylab"/>
                <xblock-include definition="html/toyjumpto"/>
                <xblock-include definition="html/toyhtml"/>
                <xblock-include definition="html/nonportable"/>
                <xblock-include definition="html/nonportable_link"/>
                <xblock-include definition="html/badlink"/>
                <xblock-include definition="html/with_styling"/>
                <xblock-include definition="html/just_img"/>
                <xblock-include definition="video/Video_Resources"/>
            </sequential>
        """)
