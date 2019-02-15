"""
django-rules for courseware related features
"""
from __future__ import absolute_import

from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

import rules


@rules.predicate
def is_verified_or_masters_track_exam(user, exam):
    """
    Returns whether the user is in a verified or master's track
    """
    course_id = CourseKey.from_string(exam['course_id'])
    mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_id)
    return is_active and mode in ('verified', 'masters')


# The edx_proctoring.api uses this permission to gate access to the
# proctored experience
can_take_proctored_exam = is_verified_or_masters_track_exam
rules.set_perm('edx_proctoring.can_take_proctored_exam', is_verified_or_masters_track_exam)
