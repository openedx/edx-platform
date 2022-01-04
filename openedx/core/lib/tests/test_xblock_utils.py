"""
Tests for xblock_utils.py
"""


import uuid
from unittest.mock import patch

import ddt
from django.conf import settings
from django.test.client import RequestFactory
from opaque_keys.edx.asides import AsideUsageKeyV1, AsideUsageKeyV2
from web_fragments.fragment import Fragment
from xblock.core import XBlockAside

from openedx.core.lib.url_utils import quote_slashes
from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies
from openedx.core.lib.xblock_utils import (
    get_aside_from_xblock,
    is_xblock_aside,
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls,
    request_token,
    sanitize_html_id,
    wrap_fragment,
    wrap_xblock
)
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.test_asides import AsideTestType  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
class TestXblockUtils(SharedModuleStoreTestCase):
    """
    Tests for xblock utility functions.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_mongo = CourseFactory.create(
            default_store=ModuleStoreEnum.Type.mongo,
            org='TestX',
            number='TS01',
            run='2015'
        )
        cls.course_split = CourseFactory.create(
            default_store=ModuleStoreEnum.Type.split,
            org='TestX',
            number='TS02',
            run='2015'
        )

    def create_fragment(self, content=None):
        """
        Create a fragment.
        """
        fragment = Fragment(content)
        fragment.add_css('body {background-color:red;}')
        fragment.add_javascript('alert("Hi!");')
        return fragment

    def test_wrap_fragment(self):
        """
        Verify that wrap_fragment adds new content.
        """
        new_content = '<p>New Content<p>'
        fragment = self.create_fragment()
        wrapped_fragment = wrap_fragment(fragment, new_content)
        assert '<p>New Content<p>' == wrapped_fragment.content
        assert 'body {background-color:red;}' == wrapped_fragment.resources[0].data
        assert 'alert("Hi!");' == wrapped_fragment.resources[1].data

    def test_request_token(self):
        """
        Verify that a proper token is returned.
        """
        request_with_token = RequestFactory().get('/')
        request_with_token._xblock_token = '123'  # pylint: disable=protected-access
        token = request_token(request_with_token)
        assert token == '123'

        request_without_token = RequestFactory().get('/')
        token = request_token(request_without_token)
        # Test to see if the token is an uuid1 hex value
        test_uuid = uuid.UUID(token, version=1)
        assert token == test_uuid.hex

    @ddt.data(
        ('course_mongo', 'data-usage-id="i4x:;_;_TestX;_TS01;_course;_2015"'),
        ('course_split', 'data-usage-id="block-v1:TestX+TS02+2015+type@course+block@course"')
    )
    @ddt.unpack
    def test_wrap_xblock(self, course_id, data_usage_id):
        """
        Verify that new content is added and the resources are the same.
        """
        fragment = self.create_fragment("<h1>Test!</h1>")
        fragment.initialize_js('BlockMain')  # wrap_block() sets some attributes only if there is JS.
        course = getattr(self, course_id)
        test_wrap_output = wrap_xblock(
            runtime_class='TestRuntime',
            block=course,
            view='baseview',
            frag=fragment,
            context={"wrap_xblock_data": {"custom-attribute": "custom-value"}},
            usage_id_serializer=lambda usage_id: quote_slashes(str(usage_id)),
            request_token=uuid.uuid1().hex
        )
        assert isinstance(test_wrap_output, Fragment)
        assert 'xblock-baseview' in test_wrap_output.content
        assert 'data-runtime-class="TestRuntime"' in test_wrap_output.content
        assert data_usage_id in test_wrap_output.content
        assert '<h1>Test!</h1>' in test_wrap_output.content
        assert 'data-custom-attribute="custom-value"' in test_wrap_output.content
        assert test_wrap_output.resources[0].data == 'body {background-color:red;}'
        assert test_wrap_output.resources[1].data == 'alert("Hi!");'

    @ddt.data('course_mongo', 'course_split')
    def test_replace_jump_to_id_urls(self, course_id):
        """
        Verify that the jump-to URL has been replaced.
        """
        course = getattr(self, course_id)
        test_replace = replace_jump_to_id_urls(
            course_id=course.id,
            jump_to_id_base_url='/base_url/',
            block=course,
            view='baseview',
            frag=Fragment('<a href="/jump_to_id/id">'),
            context=None
        )
        assert isinstance(test_replace, Fragment)
        assert test_replace.content == '<a href="/base_url/id">'

    @ddt.data(
        ('course_mongo', '<a href="/courses/TestX/TS01/2015/id">'),
        ('course_split', '<a href="/courses/course-v1:TestX+TS02+2015/id">')
    )
    @ddt.unpack
    def test_replace_course_urls(self, course_id, anchor_tag):
        """
        Verify that the course URL has been replaced.
        """
        course = getattr(self, course_id)
        test_replace = replace_course_urls(
            course_id=course.id,
            block=course,
            view='baseview',
            frag=Fragment('<a href="/course/id">'),
            context=None
        )
        assert isinstance(test_replace, Fragment)
        assert test_replace.content == anchor_tag

    @ddt.data(
        ('course_mongo', '<a href="/c4x/TestX/TS01/asset/id">'),
        ('course_split', '<a href="/asset-v1:TestX+TS02+2015+type@asset+block/id">')
    )
    @ddt.unpack
    def test_replace_static_urls(self, course_id, anchor_tag):
        """
        Verify that the static URL has been replaced.
        """
        course = getattr(self, course_id)
        test_replace = replace_static_urls(
            data_dir=None,
            course_id=course.id,
            block=course,
            view='baseview',
            frag=Fragment('<a href="/static/id">'),
            context=None
        )
        assert isinstance(test_replace, Fragment)
        assert test_replace.content == anchor_tag

    def test_sanitize_html_id(self):
        """
        Verify that colons and dashes are replaced.
        """
        dirty_string = 'I:have-un:allowed_characters'
        clean_string = sanitize_html_id(dirty_string)

        assert clean_string == 'I_have_un_allowed_characters'

    @ddt.data(
        (True, ["combined.css"]),
        (False, ["a.css", "b.css", "c.css"]),
    )
    @ddt.unpack
    def test_get_css_dependencies(self, pipeline_enabled, expected_css_dependencies):
        """
        Verify that `get_css_dependencies` returns correct list of files.
        """
        pipeline = settings.PIPELINE.copy()
        pipeline['PIPELINE_ENABLED'] = pipeline_enabled
        pipeline['STYLESHEETS'] = {
            'style-group': {
                'source_filenames': ["a.css", "b.css", "c.css"],
                'output_filename': "combined.css"
            }
        }
        with self.settings(PIPELINE=pipeline):
            css_dependencies = get_css_dependencies("style-group")
            assert css_dependencies == expected_css_dependencies

    @ddt.data(
        (True, ["combined.js"]),
        (False, ["a.js", "b.js", "c.js"]),
    )
    @ddt.unpack
    def test_get_js_dependencies(self, pipeline_enabled, expected_js_dependencies):
        """
        Verify that `get_js_dependencies` returns correct list of files.
        """
        pipeline = settings.PIPELINE.copy()
        pipeline['PIPELINE_ENABLED'] = pipeline_enabled
        pipeline['JAVASCRIPT'] = {
            'js-group': {
                'source_filenames': ["a.js", "b.js", "c.js"],
                'output_filename': "combined.js"
            }
        }
        with self.settings(PIPELINE=pipeline):
            js_dependencies = get_js_dependencies("js-group")
            assert js_dependencies == expected_js_dependencies


class TestXBlockAside(SharedModuleStoreTestCase):
    """Test the xblock aside function."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()
        cls.block = ItemFactory.create(category='aside', parent=cls.course)
        cls.aside_v2 = AsideUsageKeyV2(cls.block.scope_ids.usage_id, "aside")
        cls.aside_v1 = AsideUsageKeyV1(cls.block.scope_ids.usage_id, "aside")

    def test_is_xblock_aside(self):
        """test if xblock is aside"""
        assert is_xblock_aside(self.aside_v2) is True
        assert is_xblock_aside(self.aside_v1) is True

    def test_is_not_xblock_aside(self):
        """test if xblock is not aside"""
        assert is_xblock_aside(self.block.scope_ids.usage_id) is False

    @patch('xmodule.modulestore.xml.ImportSystem.applicable_aside_types', lambda self, block: ['test_aside'])
    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_get_aside(self):
        """test get aside success"""
        assert get_aside_from_xblock(self.block, "test_aside") is not None
