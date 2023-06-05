"""
Views to show a course outline.
"""


import datetime
import re
import six

from completion import waffle as completion_waffle
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
import edx_when.api as edx_when_api
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from waffle.models import Switch
from web_fragments.fragment import Fragment

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_overview_with_access
from lms.djangoapps.courseware.date_summary import verified_upgrade_deadline_link
from lms.djangoapps.courseware.masquerade import setup_masquerade
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from openedx.features.course_experience.utils import dates_banner_should_display
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.milestones_helpers import get_course_content_milestones
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC
from xmodule.modulestore.django import modulestore

from ..utils import get_course_outline_block_tree, get_resume_block

DEFAULT_COMPLETION_TRACKING_START = datetime.datetime(2018, 1, 24, tzinfo=UTC)


class CourseOutlineFragmentView(EdxFragmentView):
    """
    Course outline fragment to be shown in the unified course view.
    """

    def render_to_fragment(self, request, course_id, user_is_enrolled=True, **kwargs):  # pylint: disable=arguments-differ
        """
        Renders the course outline as a fragment.
        """
        from lms.urls import RESET_COURSE_DEADLINES_NAME
        from openedx.features.course_experience.urls import COURSE_HOME_VIEW_NAME

        course_key = CourseKey.from_string(course_id)
        course_overview = get_course_overview_with_access(
            request.user, 'load', course_key, check_if_enrolled=user_is_enrolled
        )
        course = modulestore().get_course(course_key)

        course_block_tree = get_course_outline_block_tree(
            request, course_id, request.user if user_is_enrolled else None
        )
        if not course_block_tree:
            return None

        resume_block = get_resume_block(course_block_tree) if user_is_enrolled else None

        if not resume_block:
            self.mark_first_unit_to_resume(course_block_tree)

        xblock_display_names = self.create_xblock_id_and_name_dict(course_block_tree)
        gated_content = self.get_content_milestones(request, course_key)

        missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, request.user)

        reset_deadlines_url = reverse(RESET_COURSE_DEADLINES_NAME)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course_overview,
            'due_date_display_format': course.due_date_display_format,
            'blocks': course_block_tree,
            'enable_links': user_is_enrolled or course.course_visibility == COURSE_VISIBILITY_PUBLIC,
            'course_key': course_key,
            'gated_content': gated_content,
            'xblock_display_names': xblock_display_names,
            'self_paced': course.self_paced,

            # We're using this flag to prevent old self-paced dates from leaking out on courses not
            # managed by edx-when.
            'in_edx_when': edx_when_api.is_enabled_for_course(course_key),
            'reset_deadlines_url': reset_deadlines_url,
            'verified_upgrade_link': verified_upgrade_deadline_link(request.user, course=course),
            'on_course_outline_page': True,
            'missed_deadlines': missed_deadlines,
            'missed_gated_content': missed_gated_content,
            'has_ended': course.has_ended(),
        }

        html = render_to_string('course_experience/course-outline-fragment.html', context)
        return Fragment(html)

    def create_xblock_id_and_name_dict(self, course_block_tree, xblock_display_names=None):
        """
        Creates a dictionary mapping xblock IDs to their names, using a course block tree.
        """
        if xblock_display_names is None:
            xblock_display_names = {}

        if not course_block_tree.get('authorization_denial_reason'):
            if course_block_tree.get('id'):
                xblock_display_names[course_block_tree['id']] = course_block_tree['display_name']

            if course_block_tree.get('children'):
                for child in course_block_tree['children']:
                    self.create_xblock_id_and_name_dict(child, xblock_display_names)

        return xblock_display_names

    def get_content_milestones(self, request, course_key):
        """
        Returns dict of subsections with prerequisites and whether the prerequisite has been completed or not
        """
        def _get_key_of_prerequisite(namespace):
            return re.sub('.gating', '', namespace)

        all_course_milestones = get_course_content_milestones(course_key)

        uncompleted_prereqs = {
            milestone['content_id']
            for milestone in get_course_content_milestones(course_key, user_id=request.user.id)
        }

        gated_content = {
            milestone['content_id']: {
                'completed_prereqs': milestone['content_id'] not in uncompleted_prereqs,
                'prerequisite': _get_key_of_prerequisite(milestone['namespace'])
            }
            for milestone in all_course_milestones
        }

        return gated_content

    def user_enrolled_after_completion_collection(self, user, course_key):
        """
        Checks that the user has enrolled in the course after 01/24/2018, the date that
        the completion API began data collection. If the user has enrolled in the course
        before this date, they may see incomplete collection data. This is a temporary
        check until all active enrollments are created after the date.
        """
        user = User.objects.get(username=user)
        try:
            user_enrollment = CourseEnrollment.objects.get(
                user=user,
                course_id=course_key,
                is_active=True
            )
            return user_enrollment.created > self._completion_data_collection_start()
        except CourseEnrollment.DoesNotExist:
            return False

    def _completion_data_collection_start(self):
        """
        Returns the date that the ENABLE_COMPLETION_TRACKING waffle switch was enabled.
        """
        # pylint: disable=protected-access
        switch_name = completion_waffle.waffle()._namespaced_name(completion_waffle.ENABLE_COMPLETION_TRACKING)
        try:
            return Switch.objects.get(name=switch_name).created
        except Switch.DoesNotExist:
            return DEFAULT_COMPLETION_TRACKING_START

    def mark_first_unit_to_resume(self, block_node):
        children = block_node.get('children')
        if children:
            children[0]['resume_block'] = True
            self.mark_first_unit_to_resume(children[0])
