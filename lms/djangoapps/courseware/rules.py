"""
django-rules and Bridgekeeper rules for courseware related features
"""
from __future__ import absolute_import

from bridgekeeper.rules import Rule
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

import rules
from course_modes.models import CourseMode
from student.models import CourseEnrollment

from .access import has_access


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
        # Return an always-empty queryset filter so that this always
        # fails permissions, but still passes the is_possible_for check
        # that is used to determine if the rule should allow a user
        # into django admin
        return Q(pk__in=[])
