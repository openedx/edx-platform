"""
This module is essentially a broker to xmodule/tabs.py -- it was originally introduced to
perform some LMS-specific tab display gymnastics for the Entrance Exams feature
"""
from django.conf import settings
from django.test.client import RequestFactory
from django.utils.translation import ugettext as _

from courseware.access import has_access
from courseware.entrance_exams import user_must_complete_entrance_exam
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

    # Now that we've loaded the tabs for this course, perform the Entrance Exam work
    # If the user has to take an entrance exam, we'll need to hide away all of the tabs
    # except for the Courseware and Instructor tabs (latter is only viewed if applicable)
    # We don't have access to the true request object in this context, but we can use a mock
    request = RequestFactory().request()
    request.user = user
    course_tab_list = []
    for tab in xmodule_tab_list:
        if user_must_complete_entrance_exam(request, user, course):
            # Hide all of the tabs except for 'Courseware' and 'Instructor'
            # Rename 'Courseware' tab to 'Entrance Exam'
            if tab.type not in ['courseware', 'instructor']:
                continue
            if tab.type == 'courseware':
                tab.name = _("Entrance Exam")
        course_tab_list.append(tab)
    return course_tab_list
