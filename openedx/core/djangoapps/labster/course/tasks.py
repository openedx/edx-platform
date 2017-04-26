"""
Labster Course tasks.
"""
from cms import CELERY_APP
from celery.utils.log import get_task_logger
from django.conf import settings

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from ccx_keys.locator import CCXLocator
from search.search_engine_base import SearchEngine
from student.roles import CourseCcxCoachRole
from student.models import CourseEnrollment

from lms.djangoapps.ccx.models import CustomCourseForEdX, CcxFieldOverride
from lms.djangoapps.instructor.enrollment import unenroll_email
from cms.djangoapps.contentstore.courseware_index import CoursewareSearchIndexer, CourseAboutSearchIndexer

from labster_course_license.models import CourseLicense
from labster_course_license.utils import update_course_access_structure


log = get_task_logger(__name__)


@CELERY_APP.task
def course_delete(course_key_string):
    """
    Cleans the course up after removing. Removes ES indexes and CCX data.
    """
    course_key = CourseKey.from_string(course_key_string)
    if settings.FEATURES.get('CUSTOM_COURSES_EDX'):
        # Remove all CCX Coaches
        coach_role = CourseCcxCoachRole(course_key)
        coach_role.remove_users(*coach_role.users_with_role())
        # Remove all course_key related CCX data
        ccxs = CustomCourseForEdX.objects.filter(course_id=course_key)
        for ccx in ccxs:
            ccx_locator = CCXLocator.from_course_locator(course_key, ccx.id)
            CcxFieldOverride.objects.filter(ccx=ccx).delete()
            enrollments = CourseEnrollment.objects.filter(course_id=ccx_locator)
            for enrollment in enrollments:
                unenroll_email(course_key, enrollment.user.email, email_students=False)
            # Remove Labster Licenses
            CourseLicense.objects.filter(course_id=ccx_locator).delete()
        ccxs.delete()
    # Remove indexes from ElasticSearch
    if CoursewareSearchIndexer.indexing_is_enabled():
        searcher = SearchEngine.get_search_engine(CoursewareSearchIndexer.INDEX_NAME)
        if searcher:
            CoursewareSearchIndexer.remove_deleted_items(searcher, course_key, [])
            searcher.remove(CourseAboutSearchIndexer.DISCOVERY_DOCUMENT_TYPE, [course_key_string])
    return "succeeded"


@CELERY_APP.task
def update_course_access(course_id):
    """
    Updates master course access structure.
    Args:
        course_id(str): A string representation of course identifier
    Returns:
        None
    """
    try:
        course_key = CourseKey.from_string(course_id)
        update_course_access_structure(course_key)
        log.info("Course %s blocks structure was updated successfully.", course_id)
    except InvalidKeyError as ex:
        log.error("Course %s error: %s", course_id, ex)
