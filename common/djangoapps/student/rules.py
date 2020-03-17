"""
Django rules for student roles
"""
from __future__ import absolute_import

import rules

from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace

from .roles import CourseDataResearcherRole

# Waffle flag to enable the separate course outline page and full width content.
RESEARCHER_ROLE = CourseWaffleFlag(WaffleFlagNamespace(name='instructor'), 'researcher')


@rules.predicate
def can_access_reports(user, course_id):
    """
    Returns whether the user can access the course data downloads.
    """
    is_staff = user.is_staff
    if RESEARCHER_ROLE.is_enabled(course_id):
        return is_staff or CourseDataResearcherRole(course_id).has_user(user)
    else:
        return is_staff or has_access(user, 'staff', course_id)

rules.add_perm('student.can_research', can_access_reports)
