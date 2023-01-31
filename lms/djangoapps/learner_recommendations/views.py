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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.catalog.utils import (
    get_course_data,
    get_course_run_details
)
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip
from openedx.features.enterprise_support.utils import is_enterprise_learner
from lms.djangoapps.learner_recommendations.toggles import enable_course_about_page_recommendations
from lms.djangoapps.learner_recommendations.utils import (
    get_algolia_courses_recommendation,
    get_amplitude_course_recommendations,
    filter_recommended_courses,
    course_data_for_discovery_card,
)


log = logging.getLogger(__name__)


class AlgoliaCoursesSearchView(APIView):
    """
    **Example Request**

    GET api/learner_recommendations/algolia/courses/{course_id}/
    """

    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_id):
        """ Retrieves course recommendations from Algolia based on course skills. """

        course_run_data = get_course_run_details(course_id, ["course"])
        course_key_str = course_run_data.get("course", None)

        # Fetching course level type and skills from discovery service.
        course_data = get_course_data(course_key_str, ["level_type", "skill_names"])

        # If discovery service fails to fetch data, we will not run recommendations engine.
        if not course_data:
            return Response({"courses": [], "count": 0}, status=200)

        course_data["key"] = course_id
        response = get_algolia_courses_recommendation(course_data)

        return Response({"courses": response.get("hits", []), "count": response.get("nbHits", 0)}, status=200)


class AmplitudeRecommendationsView(APIView):
    """
    **Example Request**

    GET api/learner_recommendations/amplitude/{course_id}/
    """

    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_id):
        """
        Recommend courses based on amplitude recommendations.
        Recommend program if user is enrolled-in any other course of program.
        """
        if not enable_course_about_page_recommendations():
            return Response("Recommendations not found", status=404)

        if is_enterprise_learner(request.user):
            raise PermissionDenied()

        recommendation_count = 4
        course_key = course_id
        split_course_key = course_key.split(":")[-1]
        split_course_id = split_course_key.split("+")[:2]
        course_id = f"{split_course_id[0]}+{split_course_id[1]}"

        try:
            is_control, has_is_control, course_keys = get_amplitude_course_recommendations(
                request.user.id, settings.COURSE_ABOUT_PAGE_AMPLITUDE_RECOMMENDATION_ID
            )
        except Exception as err:  # pylint: disable=broad-except
            log.info(f"Amplitude API failed due to: {err}")
            return Response("Recommendations not found", status=404)

        is_control = is_control if has_is_control else None

        ip_address = get_client_ip(request)[0]
        user_country_code = country_code_from_ip(ip_address).upper()
        filtered_courses = filter_recommended_courses(
            request.user, course_keys, user_country_code=user_country_code, request_course=course_id,
        )
        recommended_courses = map(course_data_for_discovery_card, filtered_courses)
        recommended_courses = recommended_courses[:recommendation_count]

        return Response({"is_control": is_control, "courses": recommended_courses}, status=200)
