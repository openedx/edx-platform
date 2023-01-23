"""
Views for Learner Recommendations.
"""

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.catalog.utils import (
    get_course_data,
    get_course_run_details
)
from lms.djangoapps.learner_recommendations.utils import (
    get_algolia_courses_recommendation
)


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
