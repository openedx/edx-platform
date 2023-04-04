"""
Additional utilities for Learner Recommendations.
"""
import logging
import requests

from algoliasearch.search_client import SearchClient
from django.conf import settings

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses
from openedx.core.djangoapps.catalog.utils import get_course_data, get_programs
from lms.djangoapps.program_enrollments.api import fetch_program_enrollments_by_student

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


def _get_user_enrolled_course_keys(user):
    """
    Returns course ids in which the user is enrolled in.
    """
    course_enrollments = CourseEnrollment.enrollments_for_user(user)
    return [str(course_enrollment.course_id) for course_enrollment in course_enrollments]


def _is_enrolled_in_course(course_runs, enrolled_course_keys):
    """
    Returns True if a user is enrolled in any course run of the course else false.
    """
    return any(course_run.get("key", None) in enrolled_course_keys for course_run in course_runs)


def _has_country_restrictions(product, user_country):
    """
    Helper method that tell whether the product (course or program) has any country restrictions.
    A product is restricted for the user if the country in which user is logged in from:
    - is in the "block list" or
    - is not in the "allow list" if the "allow list" is not empty. If it is empty, then all locations can access it.
    Args:
      product: course/program
      user_country (string): country the user is logged in from

    Returns:
        True if the product is restricted in the country and False otherwise
    """
    if not user_country:
        return False

    allow_list, block_list = [], []
    location_restriction = product.get("location_restriction", None)
    if location_restriction:
        restriction_type = location_restriction.get("restriction_type")
        countries = location_restriction.get("countries")
        if restriction_type == "allowlist":
            allow_list = countries
        elif restriction_type == "blocklist":
            block_list = countries

    return user_country in block_list or (bool(allow_list) and user_country not in allow_list)


def get_amplitude_course_recommendations(user_id, recommendation_id):
    """
    Get personalized recommendations from Amplitude.

    Args:
        user_id: The user for which the recommendations need to be pulled
        recommendation_id: Amplitude model id

    Returns:
        is_control (bool): Control group value for the user
        has_is_control (bool): Boolean value indicating if the control group for
        the user has been decided.
        recommended_course_keys (list): Course keys returned by Amplitude.
    """
    headers = {
        "Authorization": f"Api-Key {settings.AMPLITUDE_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "user_id": user_id,
        "get_recs": True,
        "rec_id": recommendation_id,
    }
    response = requests.get(settings.AMPLITUDE_URL, params=params, headers=headers)
    if response.status_code == 200:
        response = response.json()
        recommendations = response.get("userData", {}).get("recommendations", [])
        if recommendations:
            is_control = recommendations[0].get("is_control")
            has_is_control = recommendations[0].get("has_is_control")
            recommended_course_keys = recommendations[0].get("items")
            return is_control, has_is_control, recommended_course_keys

    return True, False, []


def is_user_enrolled_in_ut_austin_masters_program(user):
    """
    Checks if a user is enrolled in any masters program

    Args:
        user: The user object

    Returns:
        True if the user is enrolled in UT Austin masters program otherwise False
    """
    program_enrollments = fetch_program_enrollments_by_student(
        user=user,
        program_enrollment_statuses=ProgramEnrollmentStatuses.__ACTIVE__,
    )
    uuids = [enrollment.program_uuid for enrollment in program_enrollments]
    enrolled_programs = get_programs(uuids=uuids) or []
    for enrolled_program in enrolled_programs:
        if enrolled_program.get("type", None) == "Masters":
            authoring_organizations = enrolled_program.get("authoring_organizations", [])
            if any(org.get("key", None) == "UTAustinX" for org in authoring_organizations):
                return True
    return False


def filter_recommended_courses(
    user,
    unfiltered_course_keys,
    recommendation_count=10,
    user_country_code=None,
    request_course_key=None,
):
    """
    Returns the filtered course recommendations. The unfiltered course keys
    pass through the following filters:
        1. Remove courses that a user is already enrolled in.
        2. If user is seeing the recommendations on a course about pages, filter that course out of recommendations.
        3. Remove the courses which is restricted in user region.

    Args:
        user: The user for which the recommendations need to be pulled
        unfiltered_course_keys: recommended course keys that needs to be filtered
        recommendation_count: the maximum count of recommendations to be returned
        user_country_code: if provided, will apply location restrictions to recommendations
        request_course_key: if provided, will filter out that course from recommendations (used for course about page)

    Returns:
        filtered_recommended_courses (list): A list of filtered course objects.
    """
    filtered_recommended_courses = []
    fields = [
        "key",
        "uuid",
        "title",
        "owners",
        "image",
        "url_slug",
        "course_runs",
        "location_restriction",
        "marketing_url",
        "programs",
    ]

    # Filter out enrolled courses .
    course_keys_to_filter_out = _get_user_enrolled_course_keys(user)
    # If user is seeing the recommendations on a course about page, filter that course out of recommendations
    if request_course_key:
        course_keys_to_filter_out.append(request_course_key)

    for course_id in unfiltered_course_keys:
        if len(filtered_recommended_courses) >= recommendation_count:
            break

        course_data = get_course_data(course_id, fields, querystring={'marketable_course_runs_only': 1})
        if (
            course_data
            and course_data.get("course_runs", [])
            and not _is_enrolled_in_course(course_data.get("course_runs", []), course_keys_to_filter_out)
            and not _has_country_restrictions(course_data, user_country_code)
        ):
            filtered_recommended_courses.append(course_data)

    return filtered_recommended_courses


def get_cross_product_recommendations(course_key):
    """
    Helper method to get associated course keys based on the key passed
    """
    return settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS.get(course_key)
