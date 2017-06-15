"""
This module contains an easily-importable task that will run under lms
settings to fire off a SUBSECTION_SCORE_CHANGED signal that can be handled
by our robust grades infrastructure.
"""
from celery import task
from celery_utils.logged_task import LoggedTask


@task(base=LoggedTask)
def clear_subsection_score(user_id_to_clear, course_key, subsection_id):
    """
    A thing Eric wrote

    Come up with a better docstring as this task gets fleshed out.
    """
    from django.contrib.auth.models import User
    from lms.djangoapps.course_blocks.api import get_course_blocks
    from lms.djangoapps.grades.new.subsection_grade import ZeroSubsectionGrade
    from lms.djangoapps.grades.new.course_data import CourseData
    from lms.djangoapps.grades.signals.signals import SUBSECTION_SCORE_CHANGED
    from xmodule.modulestore.django import modulestore

    student = User.objects.get(id=user_id_to_clear)
    store = modulestore()
    course = store.get_course(course_key, depth=0),
    course_structure = get_course_blocks(student, store.make_course_usage_key(course_key))
    course_data = CourseData(student, course=course, structure=course_structure)
    subsection = course_structure[subsection_id]
    grade = ZeroSubsectionGrade(subsection, course_data)
    grade.update_or_create_model(student)

    SUBSECTION_SCORE_CHANGED.send(
        sender=None,
        course=course,
        course_structure=course_structure,
        user=student,
        subsection_grade=grade
    )
