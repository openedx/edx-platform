"""
Signal handlers supporting various gradebook use cases
"""
from django.dispatch import receiver

from courseware import grades
from courseware.signals import score_changed
from util.request import RequestMockWithoutMiddleware
from util.signals import course_deleted

from gradebook.models import StudentGradebook, StudentGradebookHistory


@receiver(score_changed)
def on_score_changed(sender, **kwargs):
    """
    Listens for a  'score_changed' signal and when observed
    recalculates the specified user's gradebook entry
    """
    from courseware.views import get_course
    user = kwargs['user']
    course_key = kwargs['course_key']
    course_descriptor = get_course(course_key, depth=None)
    request = RequestMockWithoutMiddleware().get('/')
    request.user = user
    grade_data = grades.grade(user, request, course_descriptor)
    grade = grade_data['percent']
    proforma_grade = grades.calculate_proforma_grade(grade_data, course_descriptor.grading_policy)
    try:
        gradebook_entry = StudentGradebook.objects.get(user=user, course_id=course_key)
        if gradebook_entry.grade != grade:
            gradebook_entry.grade = grade
            gradebook_entry.proforma_grade = proforma_grade
            gradebook_entry.save()
    except StudentGradebook.DoesNotExist:
        StudentGradebook.objects.create(user=user, course_id=course_key, grade=grade, proforma_grade=proforma_grade)


@receiver(course_deleted)
def on_course_deleted(sender, **kwargs):  # pylint: disable=W0613
    """
    Listens for a 'course_deleted' signal and when observed
    removes model entries for the specified course
    """
    course_key = kwargs['course_key']
    StudentGradebook.objects.filter(course_id=course_key).delete()
    StudentGradebookHistory.objects.filter(course_id=course_key).delete()
