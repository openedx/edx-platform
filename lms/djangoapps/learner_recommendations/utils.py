"""
Additional utilities for Learner Recommendations.
"""

import logging

from algoliasearch.exceptions import RequestException, AlgoliaUnreachableHostException
from algoliasearch.search_client import SearchClient
from django.conf import settings


log = logging.getLogger(__name__)

COURSE_LEVELS = [
    'Introductory',
    'Intermediate',
    'Advanced'
]


class AlgoliaClient:
    """ Class for instantiating an Algolia search client instance. """
    algolia_client = None
    algolia_app_id = settings.ALGOLIA_APP_ID
    algolia_search_api_key = settings.ALGOLIA_SEARCH_API_KEY

    @classmethod
    def get_algolia_client(cls):
        """ Get Algolia client instance. """
        if not cls.algolia_client:
            if not (cls.algolia_app_id and cls.algolia_search_api_key):
                return None

            cls.algolia_client = SearchClient.create(cls.algolia_app_id, cls.algolia_search_api_key)

        return cls.algolia_client


def get_algolia_courses_recommendation(course_data):
    """
    Get courses recommendation from Algolia search.

    Args:
        course_data (dict): Course data to create the search query.

    Returns:
        Response object with courses recommendation from Algolia search.
    """
    algolia_client = AlgoliaClient.get_algolia_client()

    search_query = " ".join(course_data["skill_names"])
    searchable_course_levels = [
        f"level:{course_level}"
        for course_level in COURSE_LEVELS
        if course_level != course_data["level_type"]
    ]
    if algolia_client and search_query:
        algolia_index = algolia_client.init_index(settings.ALGOLIA_COURSES_RECOMMENDATION_INDEX_NAME)
        try:
            # Algolia search filter criteria:
            # - Product type: Course
            # - Courses are available (enrollable)
            # - Courses should not have the same course level as the current course
            # - Exclude current course from the results
            results = algolia_index.search(
                search_query,
                {
                    "filters": f"NOT active_run_key:'{course_data['key']}'",
                    "facetFilters": ["availability:Available now", "product:Course", searchable_course_levels],
                    "optionalWords": f"{search_query}",
                }
            )

            return results
        except (AlgoliaUnreachableHostException, RequestException) as ex:
            log.warning(f"Unexpected exception while attempting to fetch courses data from Algolia: {str(ex)}")

    return {}
