"""
This module is essentially a broker to xmodule/tabs.py -- it was originally introduced to
perform some LMS-specific tab display gymnastics for the Entrance Exams feature
"""
from django.conf import settings
from django.utils.translation import ugettext as _

from courseware.access import has_access
from student.models import CourseEnrollment, EntranceExamConfiguration
from xmodule.tabs import CourseTabList

from util import milestones_helpers


def get_course_tab_list(course, user):
    """
    Retrieves the course tab list from xmodule.tabs and manipulates the set as necessary
    """
    user_is_enrolled = user.is_authenticated() and CourseEnrollment.is_enrolled(user, course.id)
    xmodule_tab_list = CourseTabList.iterate_displayable(
        course,
        settings,
        user.is_authenticated(),
        has_access(user, 'staff', course, course.id),
        user_is_enrolled
    )

    # Entrance Exams Feature
    # If the course has an entrance exam, we'll need to see if the user has not passed it
    # If so, we'll need to hide away all of the tabs except for Courseware and Instructor
    entrance_exam_mode = False
    if settings.FEATURES.get('ENTRANCE_EXAMS', False):
        if getattr(course, 'entrance_exam_enabled', False):
            course_milestones_paths = milestones_helpers.get_course_milestones_fulfillment_paths(
                unicode(course.id),
                milestones_helpers.serialize_user(user)
            )
            for __, value in course_milestones_paths.iteritems():
                if len(value.get('content', [])):
                    for content in value['content']:
                        if content == course.entrance_exam_id \
                                and not EntranceExamConfiguration.user_can_skip_entrance_exam(user, course.id):
                            entrance_exam_mode = True
                            break

    # Now that we've loaded the tabs for this course, perform the Entrance Exam mode work
    # Majority case is no entrance exam defined
    course_tab_list = []
    for tab in xmodule_tab_list:
        if entrance_exam_mode:
            # Hide all of the tabs except for 'Courseware' and 'Instructor'
            # Rename 'Courseware' tab to 'Entrance Exam'
            if tab.type not in ['courseware', 'instructor']:
                continue
            if tab.type == 'courseware':
                tab.name = _("Entrance Exam")
        course_tab_list.append(tab)
    return course_tab_list
