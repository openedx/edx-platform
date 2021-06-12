"""
General view for the Course Home that contains metadata every page needs.
"""

from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from opaque_keys.edx.keys import CourseKey  # lint-amnesty, pylint: disable=reimported

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.djangoapps.courseware_api.utils import get_celebrations_dict
from openedx.core.djangoapps.courseware_api.views import CoursewareMeta

from common.djangoapps.student.models import CourseEnrollment, UserCelebration  # lint-amnesty, pylint: disable=unused-import
from lms.djangoapps.course_api.api import course_detail
from lms.djangoapps.course_home_api.course_metadata.v1.serializers import CourseHomeMetadataSerializer
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.courseware.tabs import get_course_tab_list


class CourseHomeMetadataView(RetrieveAPIView):
    """
    **Use Cases**

        Request Course metadata details for the Course Home MFE that every page needs.

    **Example Requests**

        GET api/course_home/v1/course_metadata/{course_key}

    **Response Values**

        Body consists of the following fields:

        course_id: (str) The Course's id (Course Run key)
        username: (str) The requesting (or masqueraded) user. Returns None for an
            unauthenticated user.
        is_enrolled: (bool) Indicates if the user is enrolled in the course
        is_self_paced: (bool) Indicates if the course is self paced
        is_staff: (bool) Indicates if the user is staff
        original_user_is_staff: (bool) Indicates if the original user has staff access
            Used for when masquerading to distinguish between the original requesting user
            and the user being masqueraded as.
        number: (str) The Course's number
        org: (str) The Course's organization
        tabs: List of Course Tabs to display. They are serialized as:
            tab_id: (str) The tab's id
            title: (str) The title of the tab to display
            url: (str) The url to view the tab
        title: (str) The Course's display title
        celebrations: (dict) a dict of celebration data

    **Returns**

        * 200 on success with above fields.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    serializer_class = CourseHomeMetadataSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        original_user_is_staff = has_access(request.user, 'staff', course_key).has_access

        _, request.user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )

        username = request.user.username if request.user.username else None
        course = course_detail(request, request.user.username, course_key)
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key_string)
        user_is_enrolled = bool(enrollment and enrollment.is_active)

        courseware_meta = CoursewareMeta(course_key, request, request.user.username)
        can_load_courseware = courseware_meta.is_microfrontend_enabled_for_user()

        browser_timezone = self.request.query_params.get('browser_timezone', None)
        celebrations = get_celebrations_dict(request.user, enrollment, course, browser_timezone)

        data = {
            'course_id': course.id,
            'username': username,
            'is_staff': has_access(request.user, 'staff', course_key).has_access,
            'original_user_is_staff': original_user_is_staff,
            'number': course.display_number_with_default,
            'org': course.display_org_with_default,
            'tabs': get_course_tab_list(request.user, course),
            'title': course.display_name_with_default,
            'is_self_paced': getattr(course, 'self_paced', False),
            'is_enrolled': user_is_enrolled,
            'can_load_courseware': can_load_courseware,
            'celebrations': celebrations,
        }
        context = self.get_serializer_context()
        context['course'] = course
        context['course_overview'] = course
        context['enrollment'] = enrollment
        serializer = self.get_serializer_class()(data, context=context)
        return Response(serializer.data)
