"""
Utilities for learner_skill_levels.
"""
from logging import getLogger
from urllib.parse import urlparse

from lms.djangoapps.grades.models import PersistentCourseGrade  # lint-amnesty, pylint: disable=unused-import
from openedx.core.djangoapps.catalog.utils import (
    get_catalog_api_client,
    check_catalog_integration_and_get_user,
    get_catalog_api_base_url,

)
from openedx.core.djangoapps.catalog.utils import get_course_data, get_course_run_data
from openedx.core.lib.edx_api_utils import get_api_data

from .constants import LEVEL_TYPE_SCORE_MAPPING

LOGGER = getLogger(__name__)  # pylint: disable=invalid-name


def get_course_run_ids(user):
    """
    Returns all the course run ids of the courses that user has passed from PersistentCourseGrade model.
    """
    return list(
        PersistentCourseGrade.objects.filter(
            user_id=user.id,
            passed_timestamp__isnull=False
        ).values_list('course_id', flat=True)
    )


def generate_skill_score_mapping(user):
    """
    Generates a skill to score mapping for all the skills user has learner so far in passed courses.
    """
    # get course_run_ids of all courses the user has passed
    course_run_ids = get_course_run_ids(user)

    skill_score_mapping = {}
    for course_run_id in course_run_ids:
        # fetch course details from course run id to get course key
        course_run_data = get_course_run_data(course_run_id, ['course'])
        if course_run_data:
            # fetch course details to get level type and skills
            course_data = get_course_data(course_run_data['course'], ['skill_names', 'level_type'])
            skill_names = course_data['skill_names']
            level_type = course_data['level_type']

            # if a level_type is None for a course, we should skip that course.
            if level_type:
                score = LEVEL_TYPE_SCORE_MAPPING[level_type.capitalize()]
                for skill in skill_names:
                    if skill in skill_score_mapping:
                        # assign scores b/w 1-3 based on level type
                        # assign the larger score if skill is repeated in 2 courses
                        skill_score_mapping[skill] = max(score, skill_score_mapping[skill])
                    else:
                        skill_score_mapping.update({skill: score})
        LOGGER.info(
            "Could not find course_key for course run id [%s].", course_run_id
        )
    return skill_score_mapping


def calculate_user_skill_score(skills_with_score):
    """
    Calculates user skill score to see where the user falls in a certain job category.
    """
    # generate a dict with skill name as key and score as value
    # take only those skills that user has learned.

    if not skills_with_score:
        return 0.0

    skills_score_dict = {
        item['name']: item['score']
        for item in skills_with_score
        if item['score'] is not None
    }
    sum_of_skills = sum(skills_score_dict.values())
    skills_count = len(skills_score_dict)
    if not skills_count:
        return 0.0
    # sum of skills score in the category/ 3*no. of skills in category
    return round(sum_of_skills / (3 * skills_count), 1)


def get_skills_score(skills, learner_skill_score):
    """
    Takes each skill item in list and appends its score to it.
    For a skill that doesn't exist in learner's skills set, appends None as score.
    """
    for skill in skills:
        skill['score'] = learner_skill_score.get(skill['name'])


def update_category_user_scores_map(categories, category_user_scores_map):
    """
    Appends user's scores for each category in the dict.
    """
    for category in categories:
        category_user_scores_map[category['name']].append(category['user_score'])


def update_edx_average_score(categories, user_score_mapping):
    """
    Calculates average score for each category and appends it.
    """
    for category in categories:
        category_scores = user_score_mapping[category['name']]
        sum_score = sum(category_scores, 0.0)
        average_score = round(sum_score / len(category_scores), 1)
        category['edx_average_score'] = average_score


def get_base_url(url):
    """
    Returns the base url for any given url.
    """
    if url:
        parsed = urlparse(url)
        return f'{parsed.scheme}://{parsed.netloc}'


def get_top_skill_categories_for_job(job_id):
    """
        Retrieve top categories for the job with the given job_id.

        Arguments:
            job_id (int): id of the job about which we are retrieving information.

        Returns:
            dict with top 5 categories of specified job.
    """
    user, catalog_integration = check_catalog_integration_and_get_user(error_message_field='Skill Categories')
    if user:
        api_client = get_catalog_api_client(user)
        root_url = get_catalog_api_base_url()
        base_api_url = get_base_url(root_url)
        resource = '/taxonomy/api/v1/job-top-subcategories'
        cache_key = f'{catalog_integration.CACHE_KEY}.job-categories.{job_id}'
        data = get_api_data(
            catalog_integration,
            resource=resource,
            resource_id=job_id,
            api_client=api_client,
            base_api_url=base_api_url,
            cache_key=cache_key if catalog_integration.is_cache_enabled else None,
        )
        if data:
            return data


def get_job_holder_usernames(job_id):
    """
        Retrieve usernames of users who have the same job as given job_id.

        Arguments:
            job_id (int): id of the job for which we are retrieving usernames.

        Returns:
            list with oldest 100 users' usernames that exist in our system.
    """
    user, catalog_integration = check_catalog_integration_and_get_user(error_message_field='Job Holder Usernames')
    if user:
        api_client = get_catalog_api_client(user)
        root_url = get_catalog_api_base_url()
        base_api_url = get_base_url(root_url)
        resource = '/taxonomy/api/v1/job-holder-usernames'
        cache_key = f'{catalog_integration.CACHE_KEY}.job-holder-usernames.{job_id}'
        data = get_api_data(
            catalog_integration,
            resource=resource,
            resource_id=job_id,
            api_client=api_client,
            base_api_url=base_api_url,
            cache_key=cache_key if catalog_integration.is_cache_enabled else None,
        )
        if data:
            return data
