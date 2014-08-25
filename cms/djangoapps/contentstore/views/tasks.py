"""
This file contains celery tasks for contentstore views
"""

from celery.task import task
from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from course_action_state.models import CourseRerunState
from contentstore.utils import initialize_permissions


@task()
def rerun_course(source_course_key, destination_course_key, user_id, fields=None):
    """
    Reruns a course in a new celery task.
    """
    try:
        modulestore().clone_course(source_course_key, destination_course_key, user_id, fields=fields)

        # set initial permissions for the user to access the course.
        initialize_permissions(destination_course_key, User.objects.get(id=user_id))

        # update state: Succeeded
        CourseRerunState.objects.succeeded(course_key=destination_course_key)

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        CourseRerunState.objects.failed(course_key=destination_course_key, exception=exc)

        # cleanup any remnants of the course
        modulestore().delete_course(destination_course_key, user_id)
