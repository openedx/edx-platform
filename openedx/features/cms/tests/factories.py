import json

from opaque_keys.edx.locator import CourseLocator

from cms.djangoapps.contentstore.tasks import rerun_course as rerun_course_task
from cms.djangoapps.contentstore.utils import add_instructor
from course_action_state.models import CourseRerunState
from lms.djangoapps.courseware.courses import get_course_by_id
from openedx.features.course_card.helpers import get_related_card_id
from xmodule.course_module import CourseFields
from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.tests.factories import XModuleFactory


class CourseRerunFactory(XModuleFactory):
    """
    A factory for creating rerun from source course

    Note: This factory is only meant to be used in test environment otherwise
    set CELERY_ALWAYS_EAGER to True
    """

    # pylint: disable=unused-argument
    @classmethod
    def _create(cls, target_class, **kwargs):

        source_course_id = kwargs.pop('source_course_id', None)
        run = kwargs.pop('run', None)
        user = kwargs.pop('user', None)

        if source_course_id is None:
            raise Exception('Source course must be provided')

        if run is None:
            raise Exception('Run must be provided')

        if user is None:
            raise Exception('User must be provided')

        org = kwargs.pop('org', source_course_id.org)
        course = kwargs.pop('course', source_course_id.course)
        start = kwargs.pop('start', CourseFields.start.default)
        display_name = kwargs.pop('display_name', None)

        if not display_name:
            source_course = get_course_by_id(source_course_id)
            display_name = source_course.display_name

        rerun_course_id = CourseLocator(
            org=org, course=course, run=run
        )

        store = modulestore()
        # verify org, course and run don't already exist
        if store.has_course(rerun_course_id, ignore_case=True):
            raise DuplicateCourseError(source_course_id, rerun_course_id)

        fields = dict()

        fields['start'] = start
        if display_name:
            fields['display_name'] = display_name

        # Make sure user has instructor and staff access to the destination course
        # so the user can see the updated status for that course
        add_instructor(rerun_course_id, user, user)

        parent_course_key = get_related_card_id(source_course_id)
        # Mark the action as initiated
        CourseRerunState.objects.initiated(parent_course_key, rerun_course_id, user, display_name)

        return rerun_course_task.delay(
            unicode(source_course_id), unicode(rerun_course_id), user.id,
            json.dumps(fields, cls=EdxJSONEncoder)
        ), rerun_course_id
