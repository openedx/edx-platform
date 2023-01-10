"""
Views for learner_skill_levels.
"""
from collections import defaultdict
from copy import deepcopy

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from .api import get_learner_skill_levels
from .utils import get_top_skill_categories_for_job, get_job_holder_usernames, update_category_user_scores_map, \
    update_edx_average_score


class LearnerSkillLevelsView(APIView):
    """
        **Use Cases**

            Returns top 5 job categories for the given job. Checks which skill the user has learned via courses
            and assign scores to each skill in category. Also takes first 100 users in our system to calculate
            average score for each category.

        **Request format**

            GET /api/user/v1/skill_level/{job_id}/

        **Response Values for GET**

            If the specified job_id doesn't exist, an HTTP
            404 "Not Found" response is returned.

            If a logged in user makes a request with an existing job, an HTTP 200
            "OK" response is returned that contains a JSON string.

        **Example Request**

            GET /api/user/v1/skill_level/1/

        **Example Response**

            {
                "job": "Digital Product Manager",
                "skill_categories": [
                    {
                        "name": "Information Technology",
                        "id": 1,
                        "skills": [
                            {"id": 2, "name": "Query Languages", "score": 1},
                            {"id": 3, "name": "MongoDB", "score": 3},
                        ]
                        "user_score": 0.4, // request user's score
                        "edx_average_score": 0.7,
                        "skills_subcategories": [
                            {
                                "id": 1,
                                "name": "Databases",
                                "skills": [
                                    {"id": 2, "name": "Query Languages", "score": 1},
                                    {"id": 3, "name": "MongoDB", "score": None},
                                ]
                            },
                            {
                                "id": 2,
                                "name": "IT Management",
                                "skills": [
                                    {"id": 1, "name": "Technology Roadmap", "score": 2},
                                ]
                            },
                            // here remaining job related skills subcategories
                        ]
                    },

                    // Here more 4 skill categories
                ]
            }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, job_id):
        """
        GET /api/user/v1/skill_level/{job_id}/
        """
        # get top categories for the given job
        job_skill_categories = get_top_skill_categories_for_job(job_id)
        if not job_skill_categories:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'message': "The job id doesn't exist, enter a valid job id."}
            )

        # assign scores for every skill request user has learned
        top_categories = deepcopy(job_skill_categories['skill_categories'])
        user_category_scores = get_learner_skill_levels(
            user=request.user,
            top_categories=top_categories,
        )

        # repeat the same logic for 100 job holder users in our system
        job_holder_usernames = get_job_holder_usernames(job_id)
        users = User.objects.filter(username__in=job_holder_usernames['usernames'])

        # edx_avg_score should only be calculated if users count is greater than 5, else skip it.
        if len(users) > 5:
            # To save all the users' scores against every category to calculate average score
            category_user_scores_map = defaultdict(list)

            for user in users:
                categories = deepcopy(job_skill_categories['skill_categories'])
                categories_with_scores = get_learner_skill_levels(
                    user=user,
                    top_categories=categories,
                )
                update_category_user_scores_map(categories_with_scores, category_user_scores_map)

            update_edx_average_score(user_category_scores, category_user_scores_map)

        job_skill_categories['skill_categories'] = user_category_scores
        return Response(job_skill_categories)
