"""
Tasks associated with accessing models related to email list widget on instructor dashboard
"""
from celery import task
from instructor_task.tasks_helper import EmailWidgetTask
from instructor.views.data_access_constants import REVERSE_INCLUSION_MAP, StudentQuery
from instructor_email_widget.models import GroupedTempQueryForSubquery
from instructor_email_widget.models import StudentsForQuery, TemporaryQuery
from django.contrib.auth.models import User
from instructor.views.data_access_constants import INCLUSION_MAP, QueryType, QueryOrigin, QUERYORIGIN_MAP
from instructor.views.data_access_constants import DatabaseFields, TEMPORARY_QUERY_LIFETIME
import random
import datetime
from instructor.tasks_helper import get_problem_users, get_section_users


@task(base=EmailWidgetTask)  # pylint: disable=not-callable
def make_single_query(course_id, query, associate_group=None, origin=QueryOrigin.WIDGET):
    """
    Make a single query for student information
    """
    temp_query = TemporaryQuery(
        inclusion=INCLUSION_MAP.get(query.inclusion),
        course_id=course_id,
        module_state_key=query.entity_id,
        filter_on=query.filter,
        entity_name=query.entity_name,
        query_type=query.query_type,
        origin=QUERYORIGIN_MAP[origin],
        done=False,
    )
    temp_query.save()
    try:
        if query.query_type == QueryType.SECTION:
            students = get_section_users(course_id, query)
        else:
            students = get_problem_users(course_id, query)
        bulk_queries = []
        for student_id, dummy0 in students:
            row = StudentsForQuery(
                query=temp_query,
                inclusion=INCLUSION_MAP[query.inclusion],
                student=User.objects.filter(id=student_id)[0],
            )
            bulk_queries.append(row)
        StudentsForQuery.objects.bulk_create(bulk_queries)
        TemporaryQuery.objects.filter(id=temp_query.id).update(done=True)  # pylint: disable=no-member
        if associate_group is not None:
            grouped_temp = GroupedTempQueryForSubquery(
                grouped_id=associate_group,
                query_id=temp_query.id,   # pylint: disable=no-member
            )
            grouped_temp.save()

    except Exception as error:
        TemporaryQuery.objects.filter(id=temp_query.id).update(done=None)  # pylint: disable=no-member
        raise(error)

    #on roughly every 5th query, purge the temporary queries of anything older than
    rand = random.random()
    if rand > .8:
        purge_temporary_queries()


@task(base=EmailWidgetTask)  # pylint: disable=not-callable
def make_subqueries(course_id, group_id, queries):
    """
    Issues the subqueries associated with a group query
    """
    for query in queries:
        query = StudentQuery(
            query.query_type,
            REVERSE_INCLUSION_MAP[query.inclusion],
            course_id.make_usage_key(query.module_state_key.block_type, query.module_state_key.block_id),
            query.filter_on,
            query.entity_name,
        )
        make_single_query.apply_async(args=(course_id, query, group_id), kwargs={'origin': QueryOrigin.EMAIL})


def purge_temporary_queries():
    """
    Delete queries made more than TEMPORARY_QUERY_LIFETIME minutes ago along with the saved students from those queries
    """
    minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=TEMPORARY_QUERY_LIFETIME)
    old_queries = TemporaryQuery.objects.filter(created__lt=minutes_ago)
    saved_students = StudentsForQuery.objects.filter(query_id__in=old_queries.values_list(DatabaseFields.ID))
    saved_students.delete()
    old_queries.delete()
