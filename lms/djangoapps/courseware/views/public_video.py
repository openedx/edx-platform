from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from opaque_keys.edx.keys import UsageKey
from organizations.api import get_course_organization
from xmodule.modulestore.django import modulestore

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.util.views import ensure_valid_usage_key
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from openedx.core.lib.courses import get_course_by_id
from ..block_render import get_block_by_usage_id

RENDER_VIDEO_XBLOCK_NAME = 'render_public_video_xblock'
RENDER_VIDEO_XBLOCK_EMBED_NAME = 'render_public_video_xblock_embed'
RENDER_VIDEO_XBLOCK_NAME_FUNC = 'render_public_video_xblock_function'
RENDER_VIDEO_XBLOCK_EMBED_NAME_FUNC = 'render_public_video_xblock_embed_function'


@method_decorator(ensure_valid_usage_key, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
@method_decorator(transaction.non_atomic_requests, name='dispatch')
class BasePublicVideoXBlockView(View):
    def get(self, request, usage_key_string):
        """ Load course and video and render public view """        
        course, video_block = get_course_and_video_block(request, usage_key_string)
        template, context = self.get_template_and_context(course, video_block)
        return render_to_response(template, context)


class PublicVideoXBlockView(BasePublicVideoXBlockView):
    def get_template_and_context(self, course, video_block):
        return public_page_template_and_context(self.request, course, video_block, RENDER_VIDEO_XBLOCK_EMBED_NAME)
    
    
class PublicVideoXBlockEmbedView(BasePublicVideoXBlockView):
    def get_template_and_context(self, course, video_block):
        return embed_view_template_and_context(course, video_block)    


@require_http_methods(["GET"])
@ensure_valid_usage_key
@xframe_options_exempt
@transaction.non_atomic_requests
def render_public_video_xblock(request, usage_key_string):
    course, video_block = get_course_and_video_block(request, usage_key_string)
    template, context = public_page_template_and_context(request, course, video_block, RENDER_VIDEO_XBLOCK_EMBED_NAME_FUNC)
    return render_to_response(template, context)


@require_http_methods(["GET"])
@ensure_valid_usage_key
@xframe_options_exempt
@transaction.non_atomic_requests
def render_public_video_xblock_embed(request, usage_key_string):
    course, video_block = get_course_and_video_block(request, usage_key_string)
    template, context = embed_view_template_and_context(course, video_block)
    return render_to_response(template, context)


def public_page_template_and_context(request, course, video_block, embed_view_name):
    fragment = video_block.render('public_view', context={
        'public_video_embed': False,
    })
    course_about_page_url, enroll_url = get_public_video_cta_button_urls(request, course)
    social_sharing_metadata = get_social_sharing_metadata(course, video_block, embed_view_name)
    org_logo = get_organization_logo_from_course(course)
    context = {
        'fragment': fragment,
        'course': course,
        'org_logo': org_logo,
        'social_sharing_metadata': social_sharing_metadata,
        'learn_more_url': course_about_page_url,
        'enroll_url': enroll_url,
        'disable_window_wrap': True,
        'disable_register_button': True,
        'edx_notes_enabled': False,
        'is_learning_mfe': True,
        'is_mobile_app': False,
    }
    return 'public_video.html', context


def embed_view_template_and_context(course, video_block):
    fragment = video_block.render('public_view', context={
        'public_video_embed': True,
    })
    context = {
        'fragment': fragment,
        'course': course,
    }
    return 'public_video_share_embed.html', context
    
    
def get_course_and_video_block(request, usage_key_string):
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
            request,
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


def get_organization_logo_from_course(course):
    """
    Get organization logo for this course
    """
    course_org = get_course_organization(course.id)

    if course_org and course_org['logo']:
        return course_org['logo'].url
    return None


def get_social_sharing_metadata(course, video_block, embed_view_name):
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
            reverse(embed_view_name, kwargs={'usage_key_string': str(video_block.location)})
        )
    }


def get_public_video_cta_button_urls(request, course):
    """
    Get the links for the 'enroll' and 'learn more' buttons on the public video page
    """
    course_key = str(course.id)
    utm_params = get_utm_params(request)
    course_about_page_url = build_url(
        reverse('about_course', kwargs={'course_id': course_key}), {}, utm_params
    )
    enroll_url = build_url(
        reverse('register_user'),
        {
            'course_id': course_key,
            'enrollment_action': 'enroll',
            'email_opt_in': False,
        },
        utm_params
    )
    return course_about_page_url, enroll_url


def get_utm_params(request):
    """
    Helper function to pull all utm_ params from the request and return them as a dict
    """
    utm_params = {}
    for param, value in request.GET.items():
        if param.startswith("utm_"):
            utm_params[param] = value
    return utm_params


def build_url(base_url, params, utm_params):
    """
    Helper function to combine a base URL, params, and utm params into a full URL
    """
    if not params and not utm_params:
        return base_url
    url_parts = urlparse(base_url)
    full_params = {**params, **utm_params}
    return urlunparse((
        url_parts.scheme,
        url_parts.netloc,
        url_parts.path,
        url_parts.params,
        urlencode(full_params),
        url_parts.fragment
    ))

