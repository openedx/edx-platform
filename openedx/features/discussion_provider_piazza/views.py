from urllib.parse import quote

from django.contrib.sites.shortcuts import get_current_site
from lti_consumer.lti_1p1.contrib.django import lti_embed
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.access import get_user_role
from openedx.core.djangoapps.discussions.api.config import get_course_discussion_config
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangolib.markup import HTML
from student.models import anonymous_id_for_user

PIAZZA_LTI_LAUNCH_URL = "https://piazza.com/connect"
ROLE_MAP = {
    'student': u'Student',
    'staff': u'Administrator',
    'instructor': u'Instructor',
}
DEFAULT_ROLE = u'Student'


class PiazzaCourseTabView(EdxFragmentView):

    def render_to_fragment(self, request, course_id=None):
        course_key = CourseKey.from_string(course_id)
        context_id = quote(course_id)
        site = get_current_site(request)
        user_id = quote(anonymous_id_for_user(request.user, course_id))
        resource_link_id = quote('{}-{}'.format(
            site.domain,
            str(course_key.make_usage_key('course', course_key.run)),
        ))
        result_sourcedid = "{context}:{resource_link}:{user_id}".format(
            context=quote(context_id),
            resource_link=resource_link_id,
            user_id=user_id
        )
        role = ROLE_MAP.get(
            get_user_role(request.user, course_key),
            DEFAULT_ROLE,
        )

        course = CourseOverview.get_from_id(course_key)
        context_title = " - ".join([
            course.display_name_with_default,
            course.display_org_with_default
        ])

        discussion_config = get_course_discussion_config(course_key)

        lti_embed_html = lti_embed(
            html_element_id='piazza-discussion-provider-lti-launcher',
            lti_launch_url=PIAZZA_LTI_LAUNCH_URL,
            oauth_key=discussion_config.config["consumer_key"],
            oauth_secret=discussion_config.config["consumer_secret"],
            resource_link_id=resource_link_id,
            user_id=user_id,
            roles=role,
            context_id=context_id,
            context_title=context_title,
            context_label=context_id,
            result_sourcedid=result_sourcedid,
        )

        fragment = Fragment(
            HTML(
                """
                <iframe
                    id='piazza-discussion-provider-lti-embed'
                    srcdoc='{}'
                 >
                </iframe>
                """
            ).format(lti_embed_html)
        )
        fragment.add_css(
            """
            #piazza-discussion-provider-lti-embed {
                width: 100%;
                min-height: 400px;
                border: none;
            }
            """
        )
        return fragment
