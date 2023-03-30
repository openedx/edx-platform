from urllib.parse import urlencode, urljoin, urlparse, urlunparse
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import View
from opaque_keys.edx.keys import UsageKey

from common.djangoapps.edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.catalog.utils import (
    get_course_data,
    get_course_uuid_for_course,
)
from openedx.core.lib.courses import get_course_by_id
from common.djangoapps.util.views import ensure_valid_usage_key
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from ..block_render import get_block_by_usage_id



@method_decorator(ensure_valid_usage_key, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
@method_decorator(transaction.non_atomic_requests, name='dispatch')
class BasePublicVideoXBlockView(View):
    """
    Base functionality for public video xblock view and embed view
    """

    def get(self, _, usage_key_string):
        """ Load course and video and render public view """
        course, video_block = self.get_course_and_video_block(usage_key_string)
        template, context = self.get_template_and_context(course, video_block)
        return render_to_response(template, context)

    def get_course_and_video_block(self, usage_key_string):
        """
        Load course and video from modulestore.
        Raises 404 if:
         - video_config.public_video_share waffle flag is not enabled for this course
         - block is not video
         - block is not marked as "public_access"
         """
        usage_key = UsageKey.from_string(usage_key_string)
        usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        course_key = usage_key.course_key

        if not PUBLIC_VIDEO_SHARE.is_enabled(course_key):
            raise Http404("Video not found.")

        # usage key block type must be `video` else raise 404
        if usage_key.block_type != 'video':
            raise Http404("Video not found.")

        with modulestore().bulk_operations(course_key):
            course = get_course_by_id(course_key, 0)

            video_block, _ = get_block_by_usage_id(
                self.request,
                str(course_key),
                str(usage_key),
                disable_staff_debug_info=True,
                course=course,
                will_recheck_access=False
            )

            # Block must be marked as public to be viewed
            if not video_block.public_access:
                raise Http404("Video not found.")

        return course, video_block


@method_decorator(ensure_valid_usage_key, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
@method_decorator(transaction.non_atomic_requests, name='dispatch')
class PublicVideoXBlockView(BasePublicVideoXBlockView):
    """ View for displaying public videos """

    def get_template_and_context(self, course, video_block):
        """
        Render video xblock, gather social media metadata, and generate CTA links
        """
        fragment = video_block.render('public_view', context={
            'public_video_embed': False,
        })
        catalog_course_data = self.get_catalog_course_data(course)
        learn_more_url, enroll_url = self.get_public_video_cta_button_urls(course, catalog_course_data)
        social_sharing_metadata = self.get_social_sharing_metadata(course, video_block)
        context = {
            'fragment': fragment,
            'course': course,
            'org_logo': catalog_course_data.get('org_logo'),
            'social_sharing_metadata': social_sharing_metadata,
            'learn_more_url': learn_more_url,
            'enroll_url': enroll_url,
            'allow_iframing': True,
            'disable_window_wrap': True,
            'disable_register_button': True,
            'edx_notes_enabled': False,
            'is_learning_mfe': True,
            'is_mobile_app': False,
        }
        return 'public_video.html', context

    def get_catalog_course_data(self, course):
        """
        Get information from the catalog service for this course
        """
        course_uuid = get_course_uuid_for_course(course.id)
        if course_uuid is None:
            return {}
        catalog_course_data = get_course_data(
            course_uuid,
            ['owner', 'url_slug'],
        )
        if catalog_course_data is None:
            return {}

        return {
            'org_logo': self._get_catalog_course_owner_logo(catalog_course_data),
            'marketing_url': self._get_catalog_course_marketing_url(catalog_course_data),
        }

    def _get_catalog_course_marketing_url(self, catalog_course_data):
        """
        Helper to extract url and remove any potential utm queries.
        The discovery API includes UTM info unless you request it to not be included.
        The request for the UUIDs will cache the response within the LMS so we need
        to strip it here.
        """
        marketing_url = catalog_course_data.get('marketing_url')
        if marketing_url is None:
            return marketing_url
        url_parts = urlparse(marketing_url)
        return self._replace_url_query(url_parts, {})

    def _get_catalog_course_owner_logo(self, catalog_course_data):
        """ Helper to safely extract the course owner image url from the catalog course """
        owners_data = catalog_course_data.get('owners', [])
        if len(owners_data) == 0:
            return None
        return owners_data[0].get('logo_image_url', None)

    def get_social_sharing_metadata(self, course, video_block):
        """
        Gather the information for the meta OpenGraph and Twitter-specific tags
        """
        video_description = f"Watch a video from the course {course.display_name} "
        if course.display_organization is not None:
            video_description += f"by {course.display_organization} "
        video_description += "on edX.org"
        video_poster = video_block._poster()  # pylint: disable=protected-access

        return {
            'video_title': video_block.display_name_with_default,
            'video_description': video_description,
            'video_thumbnail': video_poster if video_poster is not None else '',
            'video_embed_url': urljoin(
                settings.LMS_ROOT_URL,
                reverse('render_public_video_xblock_embed', kwargs={'usage_key_string': str(video_block.location)})
            )
        }

    def get_learn_more_button_url(self, course, catalog_course_data, utm_params):
        """
        If the marketing site is enabled and a course has a marketing page, use that URL.
        If not, point to the `about_course` view.
        Override all with the MKTG_URL_OVERRIDES setting.
        """
        base_url = catalog_course_data.get('marketing_url', None)
        if base_url is None:
            base_url = reverse('about_course', kwargs={'course_id': str(course.id)})
        return self.build_url(base_url, {}, utm_params)

    def get_public_video_cta_button_urls(self, course, catalog_course_data):
        """
        Get the links for the 'enroll' and 'learn more' buttons on the public video page
        """
        utm_params = self.get_utm_params()
        learn_more_url = self.get_learn_more_button_url(course, catalog_course_data, utm_params)
        enroll_url = self.build_url(
            reverse('register_user'),
            {
                'course_id': str(course.id),
                'enrollment_action': 'enroll',
                'email_opt_in': False,
            },
            utm_params
        )
        return learn_more_url, enroll_url

    def get_utm_params(self):
        """
        Helper function to pull all utm_ params from the request and return them as a dict
        """
        utm_params = {}
        for param, value in self.request.GET.items():
            if param.startswith("utm_"):
                utm_params[param] = value
        return utm_params

    def build_url(self, base_url, params, utm_params):
        """
        Helper function to combine a base URL, params, and utm params into a full URL
        """
        if not params and not utm_params:
            return base_url
        parsed_url = urlparse(base_url)
        full_params = {**params, **utm_params}
        return self._replace_url_query(parsed_url, full_params)

    def _replace_url_query(self, parsed_url, query):
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query) if query else '',
            parsed_url.fragment
        ))


@method_decorator(ensure_valid_usage_key, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
@method_decorator(transaction.non_atomic_requests, name='dispatch')
class PublicVideoXBlockEmbedView(BasePublicVideoXBlockView):
    """ View for viewing public videos embedded within Twitter or other social media """
    def get_template_and_context(self, course, video_block):
        """ Render the embed view """
        fragment = video_block.render('public_view', context={
            'public_video_embed': True,
        })
        context = {
            'fragment': fragment,
            'course': course,
        }
        return 'public_video_share_embed.html', context
