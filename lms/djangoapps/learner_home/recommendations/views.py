"""
Views for Course Recommendations in Learner Home
"""
import logging

from django.conf import settings
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.toggles import show_fallback_recommendations
from common.djangoapps.track import segment
from lms.djangoapps.learner_home.recommendations.serializers import (
    CourseRecommendationSerializer,
)
from lms.djangoapps.learner_home.recommendations.utils import (
    get_personalized_course_recommendations,
)
from lms.djangoapps.learner_home.recommendations.waffle import (
    should_show_learner_home_amplitude_recommendations,
)
from openedx.core.djangoapps.catalog.utils import get_course_data


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
        recommended_courses = []
        fallback_recommendations = settings.GENERAL_RECOMMENDATIONS if show_fallback_recommendations() else []

        try:
            is_control, has_is_control, course_keys = get_personalized_course_recommendations(user_id)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(f"Cannot get recommendations from Amplitude: {ex}")
            return self._general_recommendations_response(user_id, None, fallback_recommendations)

        is_control = is_control if has_is_control else None
        if is_control or is_control is None or not course_keys:
            return self._general_recommendations_response(user_id, is_control, fallback_recommendations)

        user_enrolled_course_keys = set()
        fields = ["title", "owners", "marketing_url"]

        course_enrollments = CourseEnrollment.enrollments_for_user(request.user)
        for course_enrollment in course_enrollments:
            course_key = f"{course_enrollment.course_id.org}+{course_enrollment.course_id.course}"
            user_enrolled_course_keys.add(course_key)

        # Pick 5 course keys, excluding the user's already enrolled course(s).
        enrollable_course_keys = [
            course_key for course_key in course_keys if course_key not in user_enrolled_course_keys
        ][:5]
        for course_id in enrollable_course_keys:
            course_data = get_course_data(course_id, fields)
            if course_data:
                recommended_courses.append(
                    {
                        "course_key": course_id,
                        "title": course_data["title"],
                        "logo_image_url": course_data["owners"][0]["logo_image_url"],
                        "marketing_url": course_data.get("marketing_url"),
                    }
                )

        # If no courses are left after filtering already enrolled courses from
        # the list of amplitude recommendations, show general recommendations
        # to the user.
        if not recommended_courses:
            return self._general_recommendations_response(user_id, is_control, fallback_recommendations)

        self._emit_recommendations_viewed_event(user_id, is_control, recommended_courses)
        return Response(
            CourseRecommendationSerializer(
                {
                    "courses": recommended_courses,
                    "is_control": is_control,
                }
            ).data,
            status=200,
        )

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
            },
        )

    def _general_recommendations_response(self, user_id, is_control, recommended_courses):
        """ Helper method for general recommendations response. """
        self._emit_recommendations_viewed_event(
            user_id, is_control, recommended_courses, amplitude_recommendations=False
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
