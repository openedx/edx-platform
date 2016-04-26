"""
This module has implementation of celery tasks for learner gradebook use cases
"""
import json
import logging

from celery.task import task  # pylint: disable=import-error,no-name-in-module

from courseware import grades
from xmodule.modulestore import EdxJSONEncoder
from util.request import RequestMockWithoutMiddleware
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

from gradebook.models import StudentGradebook

log = logging.getLogger('edx.celery.task')


@task(name=u'lms.djangoapps.gradebook.tasks.update_user_gradebook')
def update_user_gradebook(course_key, user_id):
    """
    Taks to recalculate user's gradebook entry
    """
    if not isinstance(course_key, basestring):
        raise ValueError('course_key must be a string. {} is not acceptable.'.format(type(course_key)))

    course_key = CourseKey.from_string(course_key)
    try:
        user = User.objects.get(id=user_id)
        _generate_user_gradebook(course_key, user)
    except Exception as ex:
        log.exception('An error occurred while generating gradebook: %s', ex.message)
        raise


def _generate_user_gradebook(course_key, user):
    """
    Recalculates the specified user's gradebook entry
    """
    # import is local to avoid recursive import
    from courseware.views import get_course
    course_descriptor = get_course(course_key, depth=None)
    request = RequestMockWithoutMiddleware().get('/')
    request.user = user
    progress_summary = grades.progress_summary(user, request, course_descriptor, locators_as_strings=True)
    grade_summary = grades.grade(user, request, course_descriptor)
    grading_policy = course_descriptor.grading_policy
    grade = grade_summary['percent']
    proforma_grade = grades.calculate_proforma_grade(grade_summary, grading_policy)

    try:
        gradebook_entry = StudentGradebook.objects.get(user=user, course_id=course_key)
        if gradebook_entry.grade != grade:
            gradebook_entry.grade = grade
            gradebook_entry.proforma_grade = proforma_grade
            gradebook_entry.progress_summary = json.dumps(progress_summary, cls=EdxJSONEncoder)
            gradebook_entry.grade_summary = json.dumps(grade_summary, cls=EdxJSONEncoder)
            gradebook_entry.grading_policy = json.dumps(grading_policy, cls=EdxJSONEncoder)
            gradebook_entry.save()
    except StudentGradebook.DoesNotExist:
        StudentGradebook.objects.create(
            user=user,
            course_id=course_key,
            grade=grade,
            proforma_grade=proforma_grade,
            progress_summary=json.dumps(progress_summary, cls=EdxJSONEncoder),
            grade_summary=json.dumps(grade_summary, cls=EdxJSONEncoder),
            grading_policy=json.dumps(grading_policy, cls=EdxJSONEncoder)
        )
