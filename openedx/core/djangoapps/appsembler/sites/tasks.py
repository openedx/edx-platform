"""
This file contains celery tasks for contentstore views
"""
import logging
from celery.task import task
from celery.utils.log import get_task_logger

from django.contrib.auth.models import User

from opaque_keys.edx.keys import CourseKey

from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError

LOGGER = get_task_logger(__name__)
FULL_COURSE_REINDEX_THRESHOLD = 1


@task()
def clone_course(source_course_key_string, destination_course_key_string, user_id, fields=None):
    """
    Reruns a course in a new celery task.
    """
    # import here, at top level this import prevents the celery workers from starting up correctly
    from edxval.api import copy_course_videos
    from contentstore.utils import initialize_permissions
    from contentstore.courseware_index import SearchIndexingError
    from contentstore.views.course import reindex_course_and_check_access

    try:
        # deserialize the payload
        source_course_key = CourseKey.from_string(source_course_key_string)
        destination_course_key = CourseKey.from_string(destination_course_key_string)

        # use the split modulestore as the store for the rerun course,
        # as the Mongo modulestore doesn't support multiple runs of the same course.
        store = modulestore()
        with store.default_store('split'):
            store.clone_course(source_course_key, destination_course_key, user_id, fields=fields)

        # Send statistics
        from appsembler.models import update_course_statistics
        update_course_statistics()

        # set initial permissions for the user to access the course.
        user = User.objects.get(id=user_id)
        initialize_permissions(destination_course_key, user)

        # add course intructor and staff roles to the new user
        CourseInstructorRole(destination_course_key).add_users(user)
        CourseStaffRole(destination_course_key).add_users(user)

        # call edxval to attach videos to the rerun
        copy_course_videos(source_course_key, destination_course_key)

        return "succeeded"

    except DuplicateCourseError as exc:
        # do NOT delete the original course, only update the status
        logging.exception(u'Course Clone Error')
        return "duplicate course"

    except SearchIndexingError as search_err:
        logging.exception(u'Course Clone index Error')
        return "index error"

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        logging.exception(u'Course Clone Error')

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(destination_course_key, user_id)
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return "exception: " + unicode(exc)
