"""
Labster Course tasks.
"""
from celery.task import task
from django.conf import settings

from opaque_keys.edx.keys import CourseKey
from ccx_keys.locator import CCXLocator
from search.search_engine_base import SearchEngine
from student.roles import CourseCcxCoachRole

from lms.djangoapps.ccx.models import CustomCourseForEdX, CcxMembership, CcxFutureMembership, CcxFieldOverride
from lms.djangoapps.labster_course_license.models import CourseLicense
from cms.djangoapps.contentstore.utils import delete_course_and_groups
from cms.djangoapps.contentstore.courseware_index import CoursewareSearchIndexer, CourseAboutSearchIndexer


@task()
def course_delete(course_key_string, user_id):
    """
    Deletes a course.
    @TODO: It is not the best solution, but helps to avoid changes in edx code.
        It'd be great to send signal from modulestore on course deletion. In this case,
        each app can handle course deletion by itself.
    """
    course_key = CourseKey.from_string(course_key_string)
    delete_course_and_groups(course_key, user_id)
    if settings.FEATURES.get('CUSTOM_COURSES_EDX'):
        # Remove all CCX Coaches
        coach_role = CourseCcxCoachRole(course_key)
        coach_role.remove_users(*coach_role.users_with_role())
        # Remove all course_key related CCX data
        ccxs = CustomCourseForEdX.objects.filter(course_id=course_key)
        for ccx in ccxs:
            CcxMembership.objects.filter(ccx=ccx).delete()
            CcxFutureMembership.objects.filter(ccx=ccx).delete()
            CcxFieldOverride.objects.filter(ccx=ccx).delete()
            # Remove Labster Licenses
            ccx_id = CCXLocator.from_course_locator(course_key, ccx.id)
            CourseLicense.objects.filter(course_id=ccx_id).delete()
        ccxs.delete()
    # Remove indexes from ElasticSearch
    if CoursewareSearchIndexer.indexing_is_enabled():
        searcher = SearchEngine.get_search_engine(CoursewareSearchIndexer.INDEX_NAME)
        if searcher:
            CoursewareSearchIndexer.remove_deleted_items(searcher, course_key, [])
            searcher.remove(CourseAboutSearchIndexer.DISCOVERY_DOCUMENT_TYPE, course_key)
    return "succeeded"
