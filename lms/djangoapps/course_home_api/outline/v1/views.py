"""
Outline Tab Views
"""

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edx_django_utils import monitoring as monitoring_utils
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_api.blocks.transformers.blocks_api import BlocksAPITransformer
from lms.djangoapps.course_home_api.outline.v1.serializers import OutlineTabSerializer

from lms.djangoapps.course_home_api.toggles import course_home_mfe_dates_tab_is_active
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from lms.djangoapps.courseware.date_summary import TodaysDate
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.course_home_api.utils import get_microfrontend_url
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers
from openedx.features.course_experience.course_tools import CourseToolsPluginManager

from lms.djangoapps.course_blocks.api import get_course_blocks
import lms.djangoapps.course_blocks.api as course_blocks_api
from xmodule.modulestore.django import modulestore


class OutlineTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Outline Tab

    **Example Requests**

        GET api/course_home/v1/outline/{course_key}

    **Response Values**

        Body consists of the following fields:

        course_tools: List of serialized Course Tool objects. Each serialization has the following fields:
            analytics_id: (str) The unique id given to the tool.
            title: (str) The display title of the tool.
            url: (str) The link to access the tool.
        course_blocks:
            blocks: List of serialized Course Block objects. Each serialization has the following fields:
                id: (str) The usage ID of the block.
                type: (str) The type of block. Possible values the names of any
                    XBlock type in the system, including custom blocks. Examples are
                    course, chapter, sequential, vertical, html, problem, video, and
                    discussion.
                display_name: (str) The display name of the block.
                lms_web_url: (str) The URL to the navigational container of the
                    xBlock on the web LMS.
                children: (list) If the block has child blocks, a list of IDs of
                    the child blocks.

    **Returns**

        * 200 on success with above fields.
        * 403 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.

    """

    permission_classes = (IsAuthenticated,)
    serializer_class = OutlineTabSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        course_usage_key = modulestore().make_course_usage_key(course_key)

        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_metric('course_id', course_key_string)
        monitoring_utils.set_custom_metric('user_id', request.user.id)
        monitoring_utils.set_custom_metric('is_staff', request.user.is_staff)

        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)

        _, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )

        course_tools = CourseToolsPluginManager.get_enabled_course_tools(request, course_key)
        date_blocks = get_course_date_blocks(course, request.user, request, num_assignments=1)

        # User locale settings
        user_timezone_locale = user_timezone_locale_prefs(request)
        user_timezone = user_timezone_locale['user_timezone']

        dates_tab_link = request.build_absolute_uri(reverse('dates', args=[course.id]))
        if course_home_mfe_dates_tab_is_active(course.id):
            dates_tab_link = get_microfrontend_url(course_key=course.id, view_name='dates')

        transformers = BlockStructureTransformers()
        transformers += course_blocks_api.get_course_block_access_transformers(request.user)
        transformers += [
            BlocksAPITransformer(None, None, depth=3),
        ]

        course_blocks = get_course_blocks(request.user, course_usage_key, transformers, include_completion=True)

        dates_widget = {
            'course_date_blocks': [block for block in date_blocks if not isinstance(block, TodaysDate)],
            'dates_tab_link': dates_tab_link,
            'user_timezone': user_timezone,
        }

        data = {
            'course_tools': course_tools,
            'course_blocks': course_blocks,
            'dates_widget': dates_widget,
        }
        context = self.get_serializer_context()
        context['course_key'] = course_key
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)
