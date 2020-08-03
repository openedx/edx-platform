"""
Progress Tab Views
"""

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edx_django_utils import monitoring as monitoring_utils
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_home_api.progress.v1.serializers import ProgressTabSerializer

from student.models import CourseEnrollment
from lms.djangoapps.course_api.blocks.transformers.blocks_api import BlocksAPITransformer
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.courseware.access import has_access
from xmodule.modulestore.django import modulestore

from lms.djangoapps.course_blocks.api import get_course_blocks
import lms.djangoapps.course_blocks.api as course_blocks_api
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers


class ProgressTabView(RetrieveAPIView):
    """
    **Use Cases**

        Request details for the Progress Tab

    **Example Requests**

        GET api/course_home/v1/progress/{course_key}

    **Response Values**

        Body consists of the following fields:

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
        courseware_summary: List of serialized Chapters. each Chapter has the following fields:
            display_name: (str) a str of what the name of the Chapter is for displaying on the site
            subsections: List of serialized Subsections, each has the following fields:
                display_name: (str) a str of what the name of the Subsection is for displaying on the site
                due: (str) a DateTime string for when the Subsection is due
                format: (str) the format, if any, of the Subsection (Homework, Exam, etc)
                graded: (bool) whether or not the Subsection is graded
                graded_total: an object containing the following fields
                    earned: (float) the amount of points the user earned
                    possible: (float) the amount of points the user could have earned
                percent_graded: (float) the percentage of the points the user received for the subsection
                show_correctness: (str) a str representing whether to show the problem/practice scores based on due date
                show_grades: (bool) a bool for whether to show grades based on the access the user has
                url: (str) the absolute path url to the Subsection
        enrollment_mode: (str) a str representing the enrollment the user has ('audit', 'verified', ...)
        user_timezone: (str) The user's preferred timezone



    **Returns**

        * 200 on success with above fields.
        * 302 if the user is not enrolled.
        * 403 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ProgressTabSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        course_usage_key = modulestore().make_course_usage_key(course_key)

        # Enable NR tracing for this view based on course
        monitoring_utils.set_custom_metric('course_id', course_key_string)
        monitoring_utils.set_custom_metric('user_id', request.user.id)
        monitoring_utils.set_custom_metric('is_staff', request.user.is_staff)

        _, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True
        )

        user_timezone_locale = user_timezone_locale_prefs(request)
        user_timezone = user_timezone_locale['user_timezone']

        transformers = BlockStructureTransformers()
        transformers += course_blocks_api.get_course_block_access_transformers(request.user)
        transformers += [
            BlocksAPITransformer(None, None, depth=3),
        ]
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_blocks = get_course_blocks(request.user, course_usage_key, transformers, include_completion=True)

        enrollment_mode, _ = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)

        course_grade = CourseGradeFactory().read(request.user, course)
        courseware_summary = course_grade.chapter_grades.values()

        data = {
            'course_blocks': course_blocks,
            'courseware_summary': courseware_summary,
            'enrollment_mode': enrollment_mode,
            'user_timezone': user_timezone,
        }
        context = self.get_serializer_context()
        context['staff_access'] = bool(has_access(request.user, 'staff', course))
        context['course_key'] = course_key
        serializer = self.get_serializer_class()(data, context=context)

        return Response(serializer.data)
