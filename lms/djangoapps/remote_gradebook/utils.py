"""
Remote gradebook utility functions
"""

import logging
import json
from itertools import ifilter

import requests
from django.conf import settings
from django.utils.translation import ugettext as _
from openedx.core.djangolib.markup import HTML

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


def get_remote_gradebook_resp(email, course, action, files=None, **kwargs):
    """
    Sends a request to the remote gradebook and indicates a specific action.

    Returns error message, response dict
    """
    rg_url = settings.REMOTE_GRADEBOOK.get('URL')
    rg_user = settings.REMOTE_GRADEBOOK_USER
    rg_password = settings.REMOTE_GRADEBOOK_PASSWORD
    if not rg_url:
        error_msg = _("Missing required remote gradebook env setting: ") + "REMOTE_GRADEBOOK['URL']"
        return error_msg, {}
    elif not rg_user or not rg_password:
        error_msg = _(
            "Missing required remote gradebook auth settings: " +
            "REMOTE_GRADEBOOK_USER, REMOTE_GRADEBOOK_PASSWORD"
        )
        return error_msg, {}

    rg_course_settings = course.remote_gradebook or {}
    rg_name = rg_course_settings.get('name') or settings.REMOTE_GRADEBOOK.get('DEFAULT_NAME')
    if not rg_name:
        error_msg = _("No gradebook name defined in course remote_gradebook metadata and no default name set")
        return error_msg, {}

    data = dict(submit=action, gradebook=rg_name, user=email, **kwargs)
    resp = requests.post(
        rg_url,
        auth=(rg_user, rg_password),
        data=data,
        files=files,
        verify=False
    )
    if not resp.ok:
        error_header = _("Error communicating with gradebook server at {url}").format(url=rg_url)
        return HTML('<p>{error_header}</p>{content}').format(error_header=error_header, content=resp.content), {}
    return None, json.loads(resp.content)


def get_remote_gradebook_datatable_resp(user, course, action, files=None, **kwargs):
    """
    Sends a request to the remote gradebook for some action that returns a datatable.

    Returns error message, datatable dict
    """
    error_message, response_json = get_remote_gradebook_resp(user.email, course, action, files=files, **kwargs)
    if error_message:
        return error_message, {}
    response_data = response_json.get('data')  # a list of dicts
    if not response_data or response_data == [{}]:
        return _("Remote gradebook returned no results for this action ({}).").format(action), {}
    datatable = dict(
        header=response_data[0].keys(),
        data=[x.values() for x in response_data],
        retdata=response_data,
    )
    return None, datatable


def get_assignment_grade_datatable(course, assignment_name, task_progress=None):
    """
    Returns a datatable of students' grades for an assignment in the given course
    """
    if not assignment_name:
        return _("No assignment name given"), {}

    row_data = []
    current_step = {'step': 'Calculating Grades'}
    student_counter = 0
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course.id)
    total_enrolled_students = enrolled_students.count()

    for student, course_grade, error in CourseGradeFactory().iter(users=enrolled_students, course=course):
        # Periodically update task status (this is a cache write)
        student_counter += 1
        if task_progress is not None:
            task_progress.update_task_state(extra_meta=current_step)
            task_progress.attempted += 1

        log.info(
            u'%s, Current step: %s, Grade calculation in-progress for students: %s/%s',
            assignment_name,
            current_step,
            student_counter,
            total_enrolled_students
        )

        if course_grade and not error:
            matching_assignment_grade = next(
                ifilter(
                    lambda grade_section: grade_section['label'] == assignment_name,
                    course_grade.summary['section_breakdown']
                ), {}
            )
            row_data.append([student.email, matching_assignment_grade.get('percent', 0)])
            if task_progress is not None:
                task_progress.succeeded += 1
        else:
            if task_progress is not None:
                task_progress.failed += 1

    if task_progress is not None:
        task_progress.succeeded = student_counter
        task_progress.skipped = task_progress.total - task_progress.attempted
        current_step = {'step': 'Calculated Grades for {} students'.format(student_counter)}
        task_progress.update_task_state(extra_meta=current_step)

    datatable = dict(
        header=[_('External email'), assignment_name],
        data=row_data,
        title=_('Grades for assignment "{name}"').format(name=assignment_name)
    )
    return None, datatable
