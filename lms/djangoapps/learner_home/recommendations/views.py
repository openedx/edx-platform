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

        general_recommendations_response = Response(
            CourseRecommendationSerializer(
                {
                    "courses": settings.GENERAL_RECOMMENDATIONS,
                    "is_personalized_recommendation": False,
                }
            ).data,
            status=200,
        )

        try:
            user_id = request.user.id
            is_control, course_keys = get_personalized_course_recommendations(user_id)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(f"Cannot get recommendations from Amplitude: {ex}")
            return general_recommendations_response

        # Emits an event to track student dashboard page visits.
        segment.track(
            user_id,
            "edx.bi.user.recommendations.viewed",
            {
                "is_personalized_recommendation": not is_control,
            },
        )

        if is_control or not course_keys:
            return general_recommendations_response

        recommended_courses = []
        user_enrolled_course_keys = set()
        fields = ["title", "owners", "marketing_url"]

        course_enrollments = CourseEnrollment.enrollments_for_user(request.user)
        for course_enrollment in course_enrollments:
            course_key = f"{course_enrollment.course_id.org}+{course_enrollment.course_id.course}"
            user_enrolled_course_keys.add(course_key)

        # Pick 5 course keys, excluding the user's already enrolled course(s).
        enrollable_course_keys = list(
            set(course_keys).difference(user_enrolled_course_keys)
        )[:5]
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
            return general_recommendations_response

        return Response(
            CourseRecommendationSerializer(
                {
                    "courses": recommended_courses,
                    "is_personalized_recommendation": not is_control,
                }
            ).data,
            status=200,
        )
