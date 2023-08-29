"""
Test for the XBlock serialization lib's API
"""
from xml.etree import ElementTree

from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.django import contentstore, modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, upload_file_to_course
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory, ToyCourseFactory
from xmodule.util.sandboxing import DEFAULT_PYTHON_LIB_FILENAME

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

    def test_html_with_fields(self):
        """ Test an HTML Block with non-default fields like editor='raw' """
        course = CourseFactory.create(display_name='test course', run="Testing_course")
        html_block = BlockFactory.create(
            parent_location=course.location,
            category="html",
            display_name="Non-default HTML Block",
            editor="raw",
            use_latex_compiler=True,
            data="🍔",
        )
        serialized = api.serialize_xblock_to_olx(html_block)
        self.assertXmlEqual(
            serialized.olx_str,
            """
            <html
                url_name="Non-default_HTML_Block"
                display_name="Non-default HTML Block"
                editor="raw"
                use_latex_compiler="true"
            ><![CDATA[
                🍔
            ]]></html>
            """
        )

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

    def test_capa_python_lib(self):
        """ Test capa problem blocks with and without python_lib.zip """
        course = CourseFactory.create(display_name='Python Testing course', run="PY")
        upload_file_to_course(
            course_key=course.id,
            contentstore=contentstore(),
            source_file='./common/test/data/uploads/python_lib.zip',
            target_filename=DEFAULT_PYTHON_LIB_FILENAME,
        )

        regular_problem = BlockFactory.create(
            parent_location=course.location,
            category="problem",
            display_name="Problem No Python",
            max_attempts=3,
            data="<problem><optionresponse></optionresponse></problem>",
        )

        python_problem = BlockFactory.create(
            parent_location=course.location,
            category="problem",
            display_name="Python Problem",
            data='<problem>This uses python: <script type="text/python">...</script>...</problem>',
        )

        # The regular problem doesn't use python so shouldn't contain python_lib.zip:

        serialized = api.serialize_xblock_to_olx(regular_problem)
        assert not serialized.static_files
        self.assertXmlEqual(
            serialized.olx_str,
            """
            <problem display_name="Problem No Python" url_name="Problem_No_Python" max_attempts="3">
                <optionresponse></optionresponse>
            </problem>
            """
        )

        # The python problem should contain python_lib.zip:

        serialized = api.serialize_xblock_to_olx(python_problem)
        assert len(serialized.static_files) == 1
        assert serialized.static_files[0].name == "python_lib.zip"
        self.assertXmlEqual(
            serialized.olx_str,
            """
            <problem display_name="Python Problem" url_name="Python_Problem">
                This uses python: <script type="text/python">...</script>...
            </problem>
            """
        )

    def test_jsinput_extra_files(self):
        """
        Test JSInput problems with extra static files.
        """
        course = CourseFactory.create(display_name='JSInput Testing course', run="JSI")
        jsinput_files = [
            ("simple-question.html", "./common/test/data/uploads/simple-question.html"),
            ("simple-question.js", "./common/test/data/uploads/simple-question.js"),
            ("simple-question.css", "./common/test/data/uploads/simple-question.css"),
            ("image.jpg", "./common/test/data/uploads/image.jpg"),
            ("jschannel.js", "./common/static/js/capa/src/jschannel.js"),
        ]
        for filename, full_path in jsinput_files:
            upload_file_to_course(
                course_key=course.id,
                contentstore=contentstore(),
                source_file=full_path,
                target_filename=filename,
            )

        jsinput_problem = BlockFactory.create(
            parent_location=course.location,
            category="problem",
            display_name="JSInput Problem",
            data="<problem><jsinput html_file='/static/simple-question.html' /></problem>",
        )

        # The jsinput problem should contain the html_file along with extra static files:

        serialized = api.serialize_xblock_to_olx(jsinput_problem)
        assert len(serialized.static_files) == 5
        for file in serialized.static_files:
            self.assertIn(file.name, list(map(lambda f: f[0], jsinput_files)))

        self.assertXmlEqual(
            serialized.olx_str,
            """
            <problem display_name="JSInput Problem" url_name="JSInput_Problem">
                <jsinput html_file='/static/simple-question.html' />
            </problem>
            """
        )
