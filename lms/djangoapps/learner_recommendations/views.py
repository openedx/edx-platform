"""
Views for Learner Recommendations.
"""

import logging
from django.conf import settings
from ipware.ip import get_client_ip
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.track import segment
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip
from openedx.features.enterprise_support.utils import is_enterprise_learner
from lms.djangoapps.learner_recommendations.toggles import enable_course_about_page_recommendations
from lms.djangoapps.learner_recommendations.utils import (
    get_amplitude_course_recommendations,
    filter_recommended_courses,
    _has_country_restrictions,
)
from lms.djangoapps.learner_recommendations.serializers import RecommendationsSerializer, CrossProductRecommendationsSerializer
from lms.djangoapps.learner_recommendations.utils import get_cross_product_recommendations
from openedx.core.djangoapps.catalog.utils import get_course_data


log = logging.getLogger(__name__)


class AmplitudeRecommendationsView(APIView):
    """
    **Example Request**

    GET api/learner_recommendations/amplitude/{course_id}/
    """

    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    recommendations_count = 4

    def _emit_recommendations_viewed_event(
        self,
        user_id,
        is_control,
        recommended_courses,
        amplitude_recommendations=True,
    ):
        """Emits an event to track recommendation experiment views."""
        segment.track(
            user_id,
            "edx.bi.user.recommendations.viewed",
            {
                "is_control": is_control,
                "amplitude_recommendations": amplitude_recommendations,
                "course_key_array": [
                    course["key"] for course in recommended_courses
                ],
                "page": "course_about_page",
            },
        )

    def get(self, request, course_id):
        """
        Returns
            - Amplitude course recommendations
            - Upsell program if the requesting course has a related program
        """
        if not enable_course_about_page_recommendations():
            return Response(status=404)

        if is_enterprise_learner(request.user):
            raise PermissionDenied()

        user = request.user
        course_locator = CourseKey.from_string(course_id)
        course_key = f'{course_locator.org}+{course_locator.course}'

        try:
            is_control, has_is_control, course_keys = get_amplitude_course_recommendations(
                user.id, settings.COURSE_ABOUT_PAGE_AMPLITUDE_RECOMMENDATION_ID
            )
        except Exception as err:  # pylint: disable=broad-except
            log.warning(f"Amplitude API failed for {user.id} due to: {err}")
            return Response(status=404)

        is_control = is_control if has_is_control else None
        recommended_courses = []
        if not (is_control or is_control is None):
            ip_address = get_client_ip(request)[0]
            user_country_code = country_code_from_ip(ip_address).upper()
            recommended_courses = filter_recommended_courses(
                user,
                course_keys,
                user_country_code=user_country_code,
                request_course=course_key,
                recommendation_count=self.recommendations_count
            )

            for course in recommended_courses:
                course.update({
                    "active_course_run": course.get("course_runs")[0]
                })

        self._emit_recommendations_viewed_event(
            user.id, is_control, recommended_courses
        )

        return Response(
            RecommendationsSerializer(
                {
                    "courses": recommended_courses,
                    "is_control": is_control,
                }
            ).data,
            status=200,
        )


class CrossProductRecommendationsView(APIView):
    """
    **Example Request**

    GET api/learner_recommendations/cross_product/{course_id}/
    """

    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_id):
        """
        Returns cross product recommendation courses
        """
        course_locator = CourseKey.from_string(course_id)
        course_key = f'{course_locator.org}+{course_locator.course}'

        associated_course_keys = get_cross_product_recommendations(course_key)

        if associated_course_keys == None:
            return Response([], status=200)

        fields = [
            "key",
            "uuid",
            "title",
            "owners",
            "image",
            "url_slug",
            "course_type",
            "course_runs",
            "location_restriction",
        ]
        course_data = [get_course_data(key, fields) for key in associated_course_keys]

        ip_address = get_client_ip(request)[0]
        user_country_code = country_code_from_ip(ip_address).upper()

        for course in course_data:
            if _has_country_restrictions(course, user_country_code):
                course_data.remove(course)

        for course in course_data:
            course.update({
                "active_course_run": course.get("course_runs")[0]
            })

        return Response(
            CrossProductRecommendationsSerializer(
                {
                    "courses": course_data
                }
            ).data,
            status=200,
        )
