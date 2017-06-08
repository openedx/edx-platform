import re
from django.conf import settings
from django.utils.timezone import now
from course_modes.models import CourseMode
from student.models import CourseEnrollment


# List of URL patterns for pages that should include
# reminders for verification upgrade.
URLS_FOR_VERIFICATION_UPGRADE = [
    r'^/courses/{}/course/'.format(settings.COURSE_KEY_PATTERN),
    r'^/courses/{}/courseware'.format(settings.COURSE_KEY_PATTERN),
    r'^/courses/{}/progress'.format(settings.COURSE_KEY_PATTERN),
]

COOKIE_NAME = 'upsell_courses'

MAX_UPSELL_COURSE_LIST_LEN = 10


class CourseUpsellMiddleware(object):
    """
    Middleware for inserting upsell_courses cookie on enabled pages.
    """
    def process_response(self, request, response):

        if self._should_include_verification_cookie(request):
            upsell_courses = self._get_upsell_courses_for_user(request)
            self._set_upsell_courses_cookie(response, upsell_courses)
        return response

    def _should_include_verification_cookie(self, request):
        """
        Returns whether a verification cookie should be
        included for the given request.
        """
        is_nonanonymous_user = request.user and request.user.id is not None
        return is_nonanonymous_user and self.is_enabled_for_request_path(request)

    def is_enabled_for_request_path(self, request):
        """
        Returns whether a verification cookie should be
        included for the given request.
        """
        path = request.META['PATH_INFO']
        for pattern in URLS_FOR_VERIFICATION_UPGRADE:
            if re.match(pattern, path):
                return True
        return False

    def _get_upsell_courses_for_user(self, request):
        """
        Get the user's last enrollments that can be upsell.
        """
        enrollments = CourseEnrollment.enrollments_for_user(request.user)
        enrollments = enrollments.filter(mode__in=CourseMode.UPSELL_TO_VERIFIED_MODES)
        # enrollments = enrollments.filter(mode___expiration_datetime__gte=now())
        enrollments = enrollments.order_by("-created")[:MAX_UPSELL_COURSE_LIST_LEN]
        return ' '.join(unicode(enrollment.course_id) for enrollment in enrollments)

    def _set_upsell_courses_cookie(self, response, upsell_courses):
        """
        Sets the cookie with information for the given
        upsell courses for the user.
        """
        response.set_cookie(
            COOKIE_NAME,
            upsell_courses,
            max_age=24 * 60 * 60,  # set for 1 day
            domain=settings.SESSION_COOKIE_DOMAIN,
            path='/',
        )
