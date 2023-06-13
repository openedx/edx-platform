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
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from opaque_keys.edx.keys import CourseKey
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.track import segment
from common.djangoapps.student.toggles import show_fallback_recommendations
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip
from openedx.core.djangoapps.catalog.utils import get_course_data
from openedx.features.enterprise_support.utils import is_enterprise_learner

from lms.djangoapps.learner_recommendations.toggles import (
    enable_course_about_page_recommendations,
    enable_dashboard_recommendations,
)
from lms.djangoapps.learner_recommendations.utils import (
    _has_country_restrictions,
    get_amplitude_course_recommendations,
    filter_recommended_courses,
    is_user_enrolled_in_ut_austin_masters_program,
    get_cross_product_recommendations,
    get_active_course_run,
)
from lms.djangoapps.learner_recommendations.serializers import (
    AboutPageRecommendationsSerializer,
    DashboardRecommendationsSerializer,
    CrossProductAndAmplitudeRecommendationsSerializer,
    CrossProductRecommendationsSerializer,
    AmplitudeRecommendationsSerializer,
)

log = logging.getLogger(__name__)


class AboutPageRecommendationsView(APIView):
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
            - Amplitude course recommendations for course about page
        """
        if not enable_course_about_page_recommendations():
            return Response(status=404)

        if is_enterprise_learner(request.user):
            raise PermissionDenied()

        user = request.user

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
                request_course_key=course_id,
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
            AboutPageRecommendationsSerializer(
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

    def _empty_response(self):
        return Response({"courses": []}, status=200)

    def get(self, request, course_id):
        """
        Returns cross product recommendation courses
        """
        course_locator = CourseKey.from_string(course_id)
        course_key = f'{course_locator.org}+{course_locator.course}'

        associated_course_keys = get_cross_product_recommendations(course_key)

        if not associated_course_keys:
            return self._empty_response()

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
            "advertised_course_run_uuid",
        ]
        course_data = [get_course_data(key, fields) for key in associated_course_keys]
        filtered_courses = [course for course in course_data if course and course.get("course_runs")]

        ip_address = get_client_ip(request)[0]
        user_country_code = country_code_from_ip(ip_address).upper()

        unrestricted_courses = []

        for course in filtered_courses:
            if _has_country_restrictions(course, user_country_code):
                continue

            active_course_run = get_active_course_run(course)
            if active_course_run:
                course.update({"active_course_run": active_course_run})
                unrestricted_courses.append(course)

        if not unrestricted_courses:
            return self._empty_response()

        return Response(
            CrossProductRecommendationsSerializer(
                {
                    "courses": unrestricted_courses
                }).data,
            status=200
        )


class ProductRecommendationsView(APIView):
    """
    **Example Request**

    GET api/learner_recommendations/product_recommendations/
    GET api/learner_recommendations/product_recommendations/{course_id}/
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication)

    fields = [
        "title",
        "owners",
        "image",
        "url_slug",
        "course_type",
        "course_runs",
        "location_restriction",
    ]

    def _get_amplitude_recommendations(self, user, user_country_code):
        """
        Helper for getting amplitude recommendations
        """

        fallback_recommendations = settings.GENERAL_RECOMMENDATIONS[0:4]

        try:
            _, _, course_keys = get_amplitude_course_recommendations(
                user.id, settings.DASHBOARD_AMPLITUDE_RECOMMENDATION_ID
            )
        except Exception as ex:  # pylint: disable=broad-except
            log.warning(f"Cannot get recommendations from Amplitude: {ex}")
            return fallback_recommendations

        if not course_keys:
            return fallback_recommendations

        filtered_courses = filter_recommended_courses(
            user, course_keys, recommendation_count=4, user_country_code=user_country_code, course_fields=self.fields
        )

        return filtered_courses if len(filtered_courses) > 0 else fallback_recommendations

    def _get_cross_product_recommendations(self, course_key, user_country_code):
        """
        Helper for getting cross product recommendations
        """

        associated_course_keys = get_cross_product_recommendations(course_key)

        if not associated_course_keys:
            return []

        course_data = [get_course_data(key, self.fields) for key in associated_course_keys]
        filtered_cross_product_courses = []

        for course in course_data:
            if (
                course
                and course.get("course_runs", [])
                and not _has_country_restrictions(course, user_country_code)
            ):

                filtered_cross_product_courses.append(course)

        return filtered_cross_product_courses

    def _cross_product_recommendations_response(self, course_key, user, user_country_code):
        """
        Helper for collecting and forming a response for
        cross product and Amplitude recommendations
        """
        amplitude_recommendations = self._get_amplitude_recommendations(user, user_country_code)
        cross_product_recommendations = self._get_cross_product_recommendations(course_key, user_country_code)

        return Response(
            CrossProductAndAmplitudeRecommendationsSerializer(
                {
                    "crossProductCourses": cross_product_recommendations,
                    "amplitudeCourses": amplitude_recommendations
                }
            ).data,
            status=200
        )

    def _amplitude_recommendations_response(self, user, user_country_code):
        """
        Helper for collecting and forming a response for Amplitude recommendations only
        """
        amplitude_recommendations = self._get_amplitude_recommendations(user, user_country_code)

        return Response(
            AmplitudeRecommendationsSerializer({
                "amplitudeCourses": amplitude_recommendations
            }).data,
            status=200
        )

    def get(self, request, course_id=None):
        """
        Returns cross product and Amplitude recommendation courses if a course id is included,
        otherwise, returns only Amplitude recommendations
        """

        ip_address = get_client_ip(request)[0]
        user_country_code = country_code_from_ip(ip_address).upper()

        if course_id:
            course_locator = CourseKey.from_string(course_id)
            course_key = f'{course_locator.org}+{course_locator.course}'
            return self._cross_product_recommendations_response(course_key, request.user, user_country_code)

        return self._amplitude_recommendations_response(request.user, user_country_code)


class DashboardRecommendationsApiView(APIView):
    """
    API to get personalized recommendations from Amplitude.

    **Example Request**

    GET /api/learner_recommendations/courses/
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
        if not enable_dashboard_recommendations():
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
            log.warning(f"Cannot get recommendations from Amplitude: {ex}")
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
            DashboardRecommendationsSerializer(
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
