"""
Helpers for courseware app
"""
from lms.djangoapps.courseware.courses import get_courses as get_courses_core
from openedx.adg.lms.applications.models import MultilingualCourseGroup
from openedx.adg.lms.utils.env_utils import is_testing_environment


def get_courses(user):
    """
    Return courses using core method if environment is test environment else uses customized method for courses list.
    """
    return get_courses_core(user) if is_testing_environment() else MultilingualCourseGroup.objects.get_courses(user)
