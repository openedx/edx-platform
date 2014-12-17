"""
Helpers associated with tasks related to email list widget on instructor dashboard
"""
from courseware.models import StudentModule
from bulk_email.models import Optout
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from instructor.views.data_access_constants import ProblemFilters, SectionFilters, DatabaseFields
from django.db.models import Q


def get_problem_users(course_id, query):
    """
    Gets Students filtered on specified problem-specific query criteria
    """
    results = []
    if query.filter == ProblemFilters.OPENED:
        results = open_query(course_id, query)
    elif query.filter == ProblemFilters.COMPLETED:
        results = completed_query(course_id, query)
    elif query.filter == ProblemFilters.NOT_OPENED:
        results = not_open_query(course_id, query)
    elif query.filter == ProblemFilters.NOT_COMPLETED:
        results = not_completed_query(course_id, query)
    return results


def get_section_users(course_id, query):
    """
    Gets Students filtered on specified section-specific query criteria
    """
    if query.filter == SectionFilters.OPENED:
        results = open_query(course_id, query)
    elif query.filter == SectionFilters.NOT_OPENED:
        results = not_open_query(course_id, query)
    return results


def not_open_query(course_id, query):
    """
    Specific db query for sections or problems that have not been opened
    """
    ids_in_course = CourseEnrollment.objects.filter(course_id=course_id,
                                                    is_active=1,
                                                    ).values_list(DatabaseFields.USER_ID)
    total_students = User.objects.filter(id__in=ids_in_course)
    without_open = total_students.exclude(id__in=
                                          StudentModule.objects.filter(
                                              module_state_key=query.entity_id,
                                              course_id=course_id).values_list(DatabaseFields.STUDENT_ID),
                                          )
    return process_results(course_id, without_open, DatabaseFields.ID, DatabaseFields.EMAIL)


def not_completed_query(course_id, query):
    """
    Specific db query for sections or problems that are not completed
    """
    ids_in_course = CourseEnrollment.objects.filter(course_id=course_id,
                                                    is_active=1,
                                                    ).values_list(DatabaseFields.USER_ID)
    total_students = User.objects.filter(id__in=ids_in_course)

    without_completed = total_students.exclude(id__in=
                                               StudentModule.objects.filter(
                                                   module_state_key=query.entity_id,
                                                   course_id=course_id).filter(~Q(grade=None))
                                               .values_list(DatabaseFields.STUDENT_ID),
                                               )
    return process_results(course_id, without_completed, DatabaseFields.ID, DatabaseFields.EMAIL)


def completed_query(course_id, query):
    """
    Specific db query for sections or problems that are completed
    """
    queryset = StudentModule.objects.filter(module_state_key=query.entity_id,
                                            course_id=course_id,
                                            ).filter(~Q(grade=None))
    return process_results(course_id, queryset, DatabaseFields.STUDENT_ID, DatabaseFields.STUDENT_EMAIL)


def open_query(course_id, query):
    """
    Specific db query for sections or problems that are opened
    """
    queryset = StudentModule.objects.filter(module_state_key=query.entity_id, course_id=course_id)
    return process_results(course_id, queryset, DatabaseFields.STUDENT_ID, DatabaseFields.STUDENT_EMAIL)


def process_results(course_id, queryset, id_field, email_field):
    """
    Handles any intermediate filtering between specific query criteria and returning to the user
    """
    filtered_query = filter_out_students_negative(course_id, queryset)
    values = filtered_query.values_list(id_field, email_field).distinct()
    return values


def filter_out_students_negative(course_id, queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for positive queries i.e. have completed/opened because of query structure. The
    negative case is different because we start with User.object vs StudentModule
    """
    without_opt_out = queryset.exclude(id__in=Optout.objects.all().values_list(DatabaseFields.USER_ID))
    without_not_enrolled = without_opt_out.exclude(
        id__in=CourseEnrollment.objects.filter(course_id=course_id, is_active=0).values_list(DatabaseFields.USER_ID))
    return without_not_enrolled


def filter_out_students_positive(course_id, queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for negative queries i.e. not completed/not opened because of query structure. The
    positive case is different because we start with StudentModule vs User.object
    """
    without_opt_out = queryset.exclude(student_id__in=Optout.objects.all().values_list(DatabaseFields.USER_ID))
    without_not_enrolled = without_opt_out.exclude(
        student_id__in=CourseEnrollment.objects.filter(course_id=course_id, is_active=0).
        values_list(DatabaseFields.USER_ID))
    return without_not_enrolled
