"""
django-rules and Bridgekeeper rules for courseware related features
"""
from __future__ import absolute_import

from bridgekeeper.rules import Rule
from course_modes.models import CourseMode
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

from .access import has_access

import rules


@rules.predicate
def is_track_ok_for_exam(user, exam):
    """
    Returns whether the user is in an appropriate enrollment mode
    """
    course_id = CourseKey.from_string(exam['course_id'])
    mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_id)
    return is_active and mode in (CourseMode.VERIFIED, CourseMode.MASTERS, CourseMode.PROFESSIONAL)


# The edx_proctoring.api uses this permission to gate access to the
# proctored experience
can_take_proctored_exam = is_track_ok_for_exam
rules.set_perm('edx_proctoring.can_take_proctored_exam', is_track_ok_for_exam)


class HasAccessRule(Rule):
    """
    A rule that calls `has_access` to determine whether it passes
    """
    def __init__(self, action):
        self.action = action

    def check(self, user, instance=None):
        return has_access(user, self.action, instance)

    def query(self, user):
        raise NotImplementedError()
