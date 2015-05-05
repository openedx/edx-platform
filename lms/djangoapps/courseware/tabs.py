"""
This module is essentially a broker to xmodule/tabs.py -- it was originally introduced to
perform some LMS-specific tab display gymnastics for the Entrance Exams feature
"""
from django.conf import settings
from django.utils.translation import ugettext as _

from courseware.entrance_exams import user_must_complete_entrance_exam
from xmodule.tabs import CourseTabList, CourseViewTab, CourseTabManager


def get_course_tab_list(request, course):
    """
    Retrieves the course tab list from xmodule.tabs and manipulates the set as necessary
    """
    user = request.user
    xmodule_tab_list = CourseTabList.iterate_displayable(course, settings, user=user)

    # Now that we've loaded the tabs for this course, perform the Entrance Exam work
    # If the user has to take an entrance exam, we'll need to hide away all of the tabs
    # except for the Courseware and Instructor tabs (latter is only viewed if applicable)
    # We don't have access to the true request object in this context, but we can use a mock
    course_tab_list = []
    for tab in xmodule_tab_list:
        if user_must_complete_entrance_exam(request, user, course):
            # Hide all of the tabs except for 'Courseware'
            # Rename 'Courseware' tab to 'Entrance Exam'
            if tab.type is not 'courseware':
                continue
            tab.name = _("Entrance Exam")
        course_tab_list.append(tab)

    # Add in any dynamic tabs, i.e. those that are not persisted
    course_tab_list += _get_dynamic_tabs(course, user)

    return course_tab_list


def _get_dynamic_tabs(course, user):
    """
    Returns the dynamic tab types for the current user.

    Note: dynamic tabs are those that are not persisted in the course, but are
    instead added dynamically based upon the user's role.
    """
    dynamic_tabs = list()
    for tab_type in CourseTabManager.get_tab_types().values():
        if not getattr(tab_type, "is_persistent", True):
            tab = CourseViewTab(tab_type)
            if tab.is_enabled(course, settings, user=user):
                dynamic_tabs.append(tab)
    dynamic_tabs.sort(key=lambda dynamic_tab: dynamic_tab.name)
    return dynamic_tabs
