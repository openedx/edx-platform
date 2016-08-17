"""
Certificate views for open badges.
"""
from django.shortcuts import redirect, get_object_or_404

from opaque_keys.edx.locator import CourseLocator
from util.views import ensure_valid_course_key
from eventtracking import tracker
from certificates.models import BadgeAssertion


@ensure_valid_course_key
def track_share_redirect(request__unused, course_id, network, student_username):
    """
    Tracks when a user downloads a badge for sharing.
    """
    course_id = CourseLocator.from_string(course_id)
    assertion = get_object_or_404(BadgeAssertion, user__username=student_username, course_id=course_id)
    tracker.emit(
        'edx.badge.assertion.shared', {
            'course_id': unicode(course_id),
            'social_network': network,
            'assertion_id': assertion.id,
            'assertion_json_url': assertion.data['json']['id'],
            'assertion_image_url': assertion.image_url,
            'user_id': assertion.user.id,
            'enrollment_mode': assertion.mode,
            'issuer': assertion.data['issuer'],
        }
    )
    return redirect(assertion.image_url)
