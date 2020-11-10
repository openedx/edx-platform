"""
Piazza Discussion Provider views.
"""
from collections import namedtuple
from typing import Dict
from urllib.parse import quote

from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from lti_consumer.lti_1p1.contrib.django import lti_embed
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.access import get_user_role
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.discussions.api.config import get_course_discussion_config
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangolib.markup import HTML
from student.models import anonymous_id_for_user


LtiCredentials = namedtuple('LtiCredentials', ('oauth_key', 'oauth_secret'))


class LtiLaunchMixin:
    LTI_LAUNCH_URL = None
    ROLE_MAP = {
        'student': u'Student',
        'staff': u'Administrator',
        'instructor': u'Instructor',
    }
    DEFAULT_ROLE = u'Student'

    @staticmethod
    def get_additional_lti_parameters(course_key: CourseKey, request: HttpRequest) -> Dict[str, str]:
        return {}

    @staticmethod
    def get_user_id(user, course_key):
        return quote(anonymous_id_for_user(user, course_key))

    def get_lti_roles(self, user, course_key) -> str:
        return self.ROLE_MAP.get(
            get_user_role(user, course_key),
            self.DEFAULT_ROLE,
        )

    @staticmethod
    def get_context_id(course_key) -> str:
        return quote(str(course_key))

    @staticmethod
    def get_resource_link_id(course_key, request) -> str:
        site = get_current_site(request)
        return quote('{}-{}'.format(
            site.domain,
            str(course_key.make_usage_key('course', course_key.run)),
        ))

    @staticmethod
    def get_result_sourcedid(context_id, resource_link_id, user_id) -> str:
        return "{context}:{resource_link}:{user_id}".format(
            context=context_id,
            resource_link=resource_link_id,
            user_id=user_id,
        )

    @staticmethod
    def get_context_title(course_key):
        course = CourseOverview.get_from_id(course_key)
        return "{} - {}".format(
            course.display_name_with_default,
            course.display_org_with_default,
        )

    @staticmethod
    def get_oauth_credentials(course_config) -> LtiCredentials:
        raise NotImplementedError

    def get_lti_embed_code(self, course_key, request):
        discussion_config = get_course_discussion_config(course_key)
        lti_creds = self.get_oauth_credentials(discussion_config)
        user_id = self.get_user_id(request.user, course_key)
        context_id = self.get_context_id(course_key)
        resource_link_id = self.get_resource_link_id(course_key, request)
        roles = self.get_lti_roles(request.user, course_key)
        context_title = self.get_context_title(course_key)
        result_sourcedid = self.get_result_sourcedid(context_id, resource_link_id, user_id)
        additional_params = self.get_additional_lti_parameters(course_key, request)

        return lti_embed(
            html_element_id='discussion-provider-lti-launcher',
            lti_launch_url=self.LTI_LAUNCH_URL,
            oauth_key=lti_creds.oauth_key,
            oauth_secret=lti_creds.oauth_secret,
            resource_link_id=resource_link_id,
            user_id=user_id,
            roles=roles,
            context_id=context_id,
            context_title=context_title,
            context_label=context_id,
            result_sourcedid=result_sourcedid,
            **additional_params,
        )

    def render_to_fragment(self, request, course_id=None):  # pylint: disable=arguments-differ
        course_key = CourseKey.from_string(course_id)
        lti_embed_html = self.get_lti_embed_code(course_key, request)

        fragment = Fragment(
            HTML(
                """
                <iframe
                    id='discussion-provider-lti-embed'
                    srcdoc='{}'
                 >
                </iframe>
                """
            ).format(lti_embed_html)
        )
        fragment.add_css(
            """
            #discussion-provider-lti-embed {
                width: 100%;
                min-height: 400px;
                border: none;
            }
            """
        )
        return fragment


class PiazzaCourseTabView(LtiLaunchMixin, EdxFragmentView):
    LTI_LAUNCH_URL = "https://piazza.com/connect"

    @staticmethod
    def get_oauth_credentials(config):
        return LtiCredentials(
            config.config["consumer_key"],
            config.config["consumer_secret"],
        )


