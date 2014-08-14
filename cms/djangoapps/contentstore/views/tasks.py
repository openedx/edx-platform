"""
This file contains celery tasks for contentstore views
"""

from celery.task import task
from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError
from course_action_state.models import CourseRerunState
from contentstore.utils import initialize_permissions
from opaque_keys.edx.keys import CourseKey


@task()
def rerun_course(source_course_key_string, destination_course_key_string, user_id, fields=None):
    """
    Reruns a course in a new celery task.
    """
    try:
        # deserialize the keys
        source_course_key = CourseKey.from_string(source_course_key_string)
        destination_course_key = CourseKey.from_string(destination_course_key_string)

        # use the split modulestore as the store for the rerun course,
        # as the Mongo modulestore doesn't support multiple runs of the same course.
        store = modulestore()
        with store.default_store('split'):
            store.clone_course(source_course_key, destination_course_key, user_id, fields=fields)

        # set initial permissions for the user to access the course.
        initialize_permissions(destination_course_key, User.objects.get(id=user_id))

        # update state: Succeeded
        CourseRerunState.objects.succeeded(course_key=destination_course_key)

        return "succeeded"

    except DuplicateCourseError as exc:
        # do NOT delete the original course, only update the status
        CourseRerunState.objects.failed(course_key=destination_course_key, exception=exc)

        return "duplicate course"

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        CourseRerunState.objects.failed(course_key=destination_course_key, exception=exc)

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(destination_course_key, user_id)
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return "exception: " + unicode(exc)
