"""
Middleware class that supports deep-links for allows courses that allow sneakpeek.
The user will be registered anonymously, logged in, and enrolled in the course
"""
from django.core.urlresolvers import resolve
from django.http import Http404

from student.models import CourseEnrollment
from util.request import course_id_from_url
from courseware.models import CoursePreference
from student.views import _create_and_login_nonregistered_user, _check_can_enroll_in_course

DISALLOW_SNEAKPEEK_URL_NAMES = ('lti_rest_endpoints', 'xblock_handler_noauth', 'xqueue_callback')


class SneakPeekDeepLinkMiddleware(object):
    """
    Sneak Peak Deep Link Middlware
    """
    def process_request(self, request):
        """
        Only if the following are all true:
          1. request is a GET
          2. request is NOT to a URL in DISALLOW_SNEAKPEEK_URL_NAMES
          3. request.user is AnonymousUser (This middleware must be added after the AuthenticationMiddleware)
          4. request has a course context
          5. request's course allows sneakpeek
          6. request's course's enrollment period is open
        Does the following:
          1. Registers an anonymous user
          2. Login this user in
          3. Enrolls this user in the course
        """
        ### Start by testing the conditions, each of which can fail fast and return,
        ### causing the middleware to do nothing
        if request.method != "GET":
            return None

        try:
            match = resolve(request.path)
            if match.url_name in DISALLOW_SNEAKPEEK_URL_NAMES:
                return None
        except Http404:
            pass

        if request.user.is_authenticated():
            return None

        course_id = course_id_from_url(request.path)
        if not course_id:
            return None

        if not CoursePreference.course_allows_nonregistered_access(course_id):
            return None

        can_enroll, _ = _check_can_enroll_in_course(
            request.user,
            course_id,
            access_type='within_enrollment_period')

        if not can_enroll:
            return None

        ### OK. We should now do the 3 steps to get the users access to follow the deeplink
        _create_and_login_nonregistered_user(request)
        CourseEnrollment.enroll(request.user, course_id)
        return None
