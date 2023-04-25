"""
Views for Course Recommendations in Learner Home
"""
import logging

from django.conf import settings
from ipware.ip import get_client_ip
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.toggles import show_fallback_recommendations
from common.djangoapps.track import segment
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip
from lms.djangoapps.learner_home.recommendations.serializers import (
    CourseRecommendationSerializer,
)
from lms.djangoapps.learner_home.recommendations.waffle import (
    should_show_learner_home_amplitude_recommendations,
)
from lms.djangoapps.learner_recommendations.utils import (
    filter_recommended_courses,
    get_amplitude_course_recommendations,
    is_user_enrolled_in_ut_austin_masters_program,
)


logger = logging.getLogger(__name__)


class CourseRecommendationApiView(APIView):
    """
    API to get personalized recommendations from Amplitude.

    **Example Request**

    GET /api/learner_home/recommendation/courses/
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication)

    def get(self, request):
        """
        Retrieves course recommendations details.
        """
        if not should_show_learner_home_amplitude_recommendations():
            return Response(status=404)

        user_id = request.user.id

        if is_user_enrolled_in_ut_austin_masters_program(request.user):
            return self._recommendations_response(user_id, None, [], False)

        fallback_recommendations = settings.GENERAL_RECOMMENDATIONS if show_fallback_recommendations() else []

        try:
            is_control, has_is_control, course_keys = get_amplitude_course_recommendations(
                user_id, settings.DASHBOARD_AMPLITUDE_RECOMMENDATION_ID
            )
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(f"Cannot get recommendations from Amplitude: {ex}")
            return self._recommendations_response(user_id, None, fallback_recommendations, False)

        is_control = is_control if has_is_control else None
        if is_control or is_control is None or not course_keys:
            return self._recommendations_response(user_id, is_control, fallback_recommendations, False)

        ip_address = get_client_ip(request)[0]
        user_country_code = country_code_from_ip(ip_address).upper()
        filtered_courses = filter_recommended_courses(
            request.user, course_keys, user_country_code=user_country_code, recommendation_count=5
        )
        # If no courses are left after filtering already enrolled courses from
        # the list of amplitude recommendations, show general recommendations
        # to the user.
        if not filtered_courses:
            return self._recommendations_response(user_id, is_control, fallback_recommendations, False)

        recommended_courses = list(map(self._course_data, filtered_courses))
        return self._recommendations_response(user_id, is_control, recommended_courses, True)

    def _emit_recommendations_viewed_event(
        self, user_id, is_control, recommended_courses, amplitude_recommendations=True
    ):
        """Emits an event to track Learner Home page visits."""
        segment.track(
            user_id,
            "edx.bi.user.recommendations.viewed",
            {
                "is_control": is_control,
                "amplitude_recommendations": amplitude_recommendations,
                "course_key_array": [course["course_key"] for course in recommended_courses],
                "page": "dashboard",
            },
        )

    def _recommendations_response(self, user_id, is_control, recommended_courses, amplitude_recommendations):
        """ Helper method for general recommendations response. """
        self._emit_recommendations_viewed_event(
            user_id, is_control, recommended_courses, amplitude_recommendations
        )
        return Response(
            CourseRecommendationSerializer(
                {
                    "courses": recommended_courses,
                    "is_control": is_control,
                }
            ).data,
            status=200,
        )

    def _course_data(self, course):
        """Helper method for personalized recommendation response"""
        return {
            "course_key": course.get("key"),
            "title": course.get("title"),
            "logo_image_url": course.get("owners")[0]["logo_image_url"] if course.get(
                "owners") else "",
            "marketing_url": course.get("marketing_url"),
        }
