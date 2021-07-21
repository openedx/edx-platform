"""
Utils for use in enrollment code
"""
import logging
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort, get_cohort_by_name

logger = logging.getLogger(__name__)


def add_user_to_course_cohort(cohort_name, course_id, user):
    """
    If cohort_name is provided, adds user to the cohort
    """
    if cohort_name is not None:
        cohort = get_cohort_by_name(course_id, cohort_name)
        try:
            add_user_to_cohort(cohort, user)
        except ValueError:
            # user already in cohort, probably because they were un-enrolled and re-enrolled
            logger.exception('Cohort re-addition')
