"""
Tests courseware views.py
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import ddt
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from openedx.core.djangoapps.waffle_utils.models import WaffleFlagCourseOverrideModel
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

from lms.djangoapps.courseware.views.public_video import (
    BasePublicVideoXBlockView,
    PublicVideoXBlockView,
    PublicVideoXBlockEmbedView,
)
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE


class TestBasePublicVideoXBlock(ModuleStoreTestCase):
    """
    Tests for public video xblock.
    """
    def setup_course(self, enable_waffle=True):
        """
        Helper method to create the course.
        """
        # pylint:disable=attribute-defined-outside-init

        with self.store.default_store(self.store.default_modulestore.get_modulestore_type()):
            self.course = CourseFactory.create(**{'start': datetime.now() - timedelta(days=1)})
            chapter = BlockFactory.create(parent=self.course, category='chapter')
            vertical_block = BlockFactory.create(
                parent_location=chapter.location,
                category='vertical',
                display_name="Vertical"
            )
            self.html_block = BlockFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='html',
                data="<p>Test HTML Content<p>"
            )
            self.video_block_public = BlockFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='video',
                display_name='Video with public access',
                metadata={'public_access': True}
            )
            self.video_block_not_public = BlockFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='video',
                display_name='Video with private access'
            )
        WaffleFlagCourseOverrideModel.objects.create(
            waffle_flag=PUBLIC_VIDEO_SHARE.name,
            course_id=self.course.id,
            enabled=enable_waffle,
        )


@ddt.ddt
class TestRenderPublicVideoXBlock(TestBasePublicVideoXBlock):
    """
    Tests for the courseware.render_public_video_xblock endpoint.
    """
    def get_response(self, usage_key, is_embed):
        """
        Overridable method to get the response from the endpoint that is being tested.
        """
        view_name = 'render_public_video_xblock'
        if is_embed:
            view_name += '_embed'
        url = reverse(view_name, kwargs={'usage_key_string': str(usage_key)})
        return self.client.get(url)

    @ddt.data(True, False)
    def test_render_xblock_with_invalid_usage_key(self, is_embed):
        """
        Verify that endpoint returns expected response with invalid usage key
        """
        response = self.get_response(usage_key='some_invalid_usage_key', is_embed=is_embed)
        self.assertContains(response, 'Page not found', status_code=404)

    @ddt.data(True, False)
    def test_render_xblock_with_non_video_usage_key(self, is_embed):
        """
        Verify that endpoint returns expected response if usage key block type is not `video`
        """
        self.setup_course()
        response = self.get_response(usage_key=self.html_block.location, is_embed=is_embed)
        self.assertContains(response, 'Page not found', status_code=404)

    @ddt.unpack
    @ddt.data(
        (True, True, 200),
        (True, False, 404),
        (False, True, 404),
        (False, False, 404),
    )
    def test_access(self, is_waffle_enabled, is_public_video, expected_status_code):
        """ Tests for access control """
        self.setup_course(enable_waffle=is_waffle_enabled)
        target_video = self.video_block_public if is_public_video else self.video_block_not_public

        response = self.get_response(usage_key=target_video.location, is_embed=False)
        embed_response = self.get_response(usage_key=target_video.location, is_embed=True)

        self.assertEqual(expected_status_code, response.status_code)
        self.assertEqual(expected_status_code, embed_response.status_code)

@ddt.ddt
class TestBasePublicVideoXBlockView(TestBasePublicVideoXBlock):
    """Test Base Public Video XBlock View tests"""
    base_block = BasePublicVideoXBlockView(request=MagicMock())

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    @patch('lms.djangoapps.courseware.views.public_video.get_block_by_usage_id')
    def test_get_course_and_video_block(self, is_waffle_enabled, is_public_video, mock_get_block_by_usage_id):
        """
        Test that get_course_and_video_block returns course and video block.
        """

        self.setup_course(enable_waffle=is_waffle_enabled)
        target_video = self.video_block_public if is_public_video else self.video_block_not_public

        mock_get_block_by_usage_id.return_value = (target_video, None)

        # get 404 unless waffle is enabled and video is public
        if is_public_video and is_waffle_enabled:
            course, video_block = self.base_block.get_course_and_video_block(str(target_video.location))
            assert course.id == self.course.id
            assert video_block.location == target_video.location
        else:
            with self.assertRaisesRegex(Http404, "Video not found"):
                course, video_block = self.base_block.get_course_and_video_block(str(target_video.location))


@ddt.ddt
class TestPublicVideoXBlockView(TestBasePublicVideoXBlock):
    """Test Public Video XBlock View"""
    request = RequestFactory().get('/?utm_source=edx.org&utm_medium=referral&utm_campaign=video')
    base_block = PublicVideoXBlockView(request=request)
    default_utm_params = {'utm_source': 'edx.org', 'utm_medium': 'referral', 'utm_campaign': 'video'}

    @contextmanager
    def mock_get_learn_more_url(self, **kwargs):
        """ Helper for mocking get_learn_more_button_url """
        with patch.object(
            PublicVideoXBlockView,
            'get_learn_more_button_url',
            **kwargs
        ) as mock_get_url:
            yield mock_get_url

    @contextmanager
    def mock_get_catalog_course_data(self, **kwargs):
        """ Helper for mocking get_catalog_course_data """
        with patch.object(
            PublicVideoXBlockView,
            'get_catalog_course_data',
            **kwargs
        ) as mock_get_data:
            yield mock_get_data

    def test_get_template_and_context(self):
        """
        Get template and context.
        """
        self.setup_course(enable_waffle=True)
        fragment = MagicMock()
        with patch.object(self.video_block_public, "render", return_value=fragment):
            with self.mock_get_learn_more_url():
                with self.mock_get_catalog_course_data():
                    template, context = self.base_block.get_template_and_context(self.course, self.video_block_public)
        assert template == 'public_video.html'
        assert context['fragment'] == fragment
        assert context['course'] == self.course

    @ddt.unpack
    @ddt.data(
        (None, None, {}),
        ('uuid', None, {}),
        ('uuid', {}, {'org_logo': None, 'marketing_url': None}),
    )
    def test_get_catalog_course_data(self, mock_get_uuid, mock_get_data, expected_response):
        self.setup_course()
        with patch(
            'lms.djangoapps.courseware.views.public_video.get_course_uuid_for_course', 
            return_value=mock_get_uuid
        ):
            with patch(
                'lms.djangoapps.courseware.views.public_video.get_course_data',
                return_value=mock_get_data
            ):
                assert self.base_block.get_catalog_course_data(self.course) == expected_response

    @ddt.unpack
    @ddt.data(
        ({}, None),
        ({'marketing_url': 'www.somesite.com/this'}, 'www.somesite.com/this'),
        ({'marketing_url': 'www.somesite.com/this?utm_source=jansen'}, 'www.somesite.com/this'),
    )
    def test_get_catalog_course_marketing_url(self, input_data, expected_url):
        url = self.base_block._get_catalog_course_marketing_url(input_data)
        assert url == expected_url

    @ddt.unpack
    @ddt.data(
        ({}, None),
        ({'owners': []}, None),
        ({'owners': [{}]}, None),
        ({'owners': [{'logo_image_url': 'somesite.org/image'}]}, 'somesite.org/image'),
        ({'owners': [{'logo_image_url': 'firsturl'}, {'logo_image_url': 'secondurl'}]}, 'firsturl'),
    )
    def test_get_catalog_course_owner_logo(self, input_data, expected_url):
        url = self.base_block._get_catalog_course_owner_logo(input_data)
        assert url == expected_url

    @ddt.data("poster", None)
    def test_get_social_sharing_metadata(self, poster_url):
        """
        Test that get_social_sharing_metadata returns correct metadata.
        """
        self.setup_course(enable_waffle=True)
        # can't mock something that doesn't exist
        self.video_block_public._post = MagicMock(return_value=poster_url)

        metadata = self.base_block.get_social_sharing_metadata(self.course, self.video_block_public)
        assert metadata["video_title"] == self.video_block_public.display_name_with_default
        assert metadata["video_description"] == f"Watch a video from the course {self.course.display_name} on edX.org"
        assert metadata["video_thumbnail"] == "" if poster_url is None else poster_url

    def test_get_utm_params(self):
        """
        Test that get_utm_params returns correct utm params.
        """
        utm_params = self.base_block.get_utm_params()
        assert utm_params == {
            'utm_source': 'edx.org',
            'utm_medium': 'referral',
            'utm_campaign': 'video',
        }

    def test_build_url(self):
        """
        Test that build_url returns correct url.
        """
        base_url = 'http://test.server'
        params = {
            'param1': 'value1',
            'param2': 'value2',
        }
        utm_params = {
            "utm_source": "edx.org",
        }
        url = self.base_block.build_url(base_url, params, utm_params)
        assert url == 'http://test.server?param1=value1&param2=value2&utm_source=edx.org'

    def assert_url_with_params(self, url, base_url, params):
        if params:
            assert url == base_url + '?' + urlencode(params)
        else:
            assert url == base_url

    @ddt.data({}, {'marketing_url': 'some_url'})
    def test_get_learn_more_button_url(self, catalog_course_info):
        """
        If we have a marketing url from the catalog service, use that. Otherwise
        use the courseware about_course
        """
        self.setup_course()
        url = self.base_block.get_learn_more_button_url(self.course, catalog_course_info, self.default_utm_params)
        if 'marketing_url' in catalog_course_info:
            expected_url = catalog_course_info['marketing_url']
        else:
            expected_url = reverse('about_course', kwargs={'course_id': str(self.course.id)})
        self.assert_url_with_params(url, expected_url, self.default_utm_params)


class TestPublicVideoXBlockEmbedView(TestBasePublicVideoXBlock):
    """Test Public Video XBlock Embed View"""
    base_block = PublicVideoXBlockEmbedView()

    def test_get_template_and_context(self):
        """
        Get template and context.
        """
        self.setup_course(enable_waffle=True)
        fragment = MagicMock()
        with patch.object(self.video_block_public, "render", return_value=fragment):
            template, context = self.base_block.get_template_and_context(self.course, self.video_block_public)
            assert template == 'public_video_share_embed.html'
            assert context['fragment'] == fragment
            assert context['course'] == self.course
