"""
Methods associated with accessing models related to email list widget on instructor dashboard
"""
from instructor_email_widget.models import GroupedQuery, SubqueryForGroupedQuery, GroupedTempQueryForSubquery
from instructor_email_widget.models import SavedQuery, StudentsForQuery, TemporaryQuery
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from django.db import transaction
from instructor.views.data_access_constants import INCLUSION_MAP
from instructor.views.data_access_constants import Inclusion, QueryStatus
from instructor.views.data_access_constants import DatabaseFields, TEMPORARY_QUERY_LIFETIME
from django.db.models import Q
from collections import defaultdict
import datetime
from instructor.tasks import make_subqueries


def delete_saved_query(query_id_to_delete):
    """
    Deletes a specified grouped query along with its saved queries
    """
    grouped_query = GroupedQuery.objects.filter(id=query_id_to_delete)
    subqueries_to_delete = SubqueryForGroupedQuery.objects.filter(grouped_id=query_id_to_delete)
    queries_saved = SavedQuery.objects.filter(id__in=subqueries_to_delete.values_list(DatabaseFields.QUERY_ID))
    #Needs to be in this specific order for deletion
    queries_saved.delete()
    subqueries_to_delete.delete()
    grouped_query.delete()


def delete_temporary_query(query_to_delete):
    """
    Removes a single query from the temporary queries
    """
    queries_to_delete = TemporaryQuery.objects.filter(id=query_to_delete)
    saved_students = StudentsForQuery.objects.filter(query_id=query_to_delete)
    saved_students.delete()
    queries_to_delete.delete()


def delete_temporary_queries_batch(query_to_delete):
    """
    Removes many queries from the temporary query table
    """
    if len(query_to_delete) == 0 or query_to_delete[0] == u'':
        return
    query_set = set(query_to_delete)
    temp_query = TemporaryQuery.objects.filter(id__in=query_set)
    saved_students = StudentsForQuery.objects.filter(query_id__in=query_set)
    saved_students.delete()
    temp_query.delete()


def delete_group_temp_queries_and_students(group_id):
    """
    Deletes "temporary" students and "temporary" subqueries associated with a group query for efficiency.
    Meant to be called after get_group_query_students has finished and the results are consumed.
    This call is not strictly necessary because the temporary entries are periodically purged.
    """
    subqueries = GroupedTempQueryForSubquery.objects.filter(grouped_id=group_id).distinct()
    subqueries_ids = subqueries.values_list('query', flat=True)
    old_queries = TemporaryQuery.objects.filter(id__in=list(subqueries_ids))
    saved_students = StudentsForQuery.objects.filter(query_id__in=old_queries.values_list(DatabaseFields.ID))
    saved_students.delete()
    old_queries.delete()
    subqueries.delete()


def save_query(course_id, saved_name, queries):
    """
    Makes a new grouped query by saving the individual subqueries and then associating them to a grouped query
    """
    if saved_name is None:
        saved_name = ""
    temp_queries = TemporaryQuery.objects.filter(id__in=queries)
    group = GroupedQuery(course_id=course_id, title=saved_name)
    group.save()
    for temp_query in temp_queries:
        perm_query = SavedQuery(
            inclusion=temp_query.inclusion,
            course_id=course_id,
            module_state_key=temp_query.module_state_key,
            filter_on=temp_query.filter_on,
            entity_name=temp_query.entity_name,
            query_type=temp_query.query_type,
        )
        perm_query.save()
        relation = SubqueryForGroupedQuery(grouped=group, query=perm_query)
        relation.save()
    return group


def save_group_name(group_id, group_name):
    """
    Assigns group_name to an already-saved group with id = group_id
    """
    group = GroupedQuery.objects.get(id=group_id)
    group.title = group_name
    group.save()
    return True


def get_group_query_students(course_id, group_id):
    """
    Asynchronously makes the subqueries for a group and then aggregates them once the subqueries are finished.
    """
    _group, queries, _relation = get_saved_queries(course_id, group_id)
    # wait for the queries to finish before proceeding
    make_subqueries.apply_async(args=(course_id, group_id, queries)).get()
    queried_students = retrieve_grouped_query(course_id, group_id)
    return queried_students


def retrieve_grouped_query(course_id, group_id):
    """
    For a grouped query where its subqueries have already been executed, return the students associated
    To optimize this in the future, we can use the read-only DB instead after making sure all previous
    data has been written
    """
    subqueries = GroupedTempQueryForSubquery.objects.filter(grouped_id=group_id).distinct()
    existing = []
    for sub in subqueries:
        existing.append(sub.query_id)
    student_info = make_existing_query(course_id, existing)
    if not student_info:
        return User.objects.none()
    students = student_info.distinct()
    return students


def get_saved_queries(course_id, specific_group=None):
    """
    Get existing saved queries associated with a given course
    """
    if specific_group:
        group = GroupedQuery.objects.filter(course_id=course_id, id=specific_group)
    else:
        group = GroupedQuery.objects.filter(course_id=course_id)
    if len(group) == 0:
        return ([], [], [])
    relation = SubqueryForGroupedQuery.objects.filter(grouped__in=group)
    queries = SavedQuery.objects.filter(id__in=relation.values_list(DatabaseFields.QUERY))
    return (group, queries, relation)


def get_temp_queries(course_id):
    """
    Get temporary queries associated with a course
    """
    queries_temp = TemporaryQuery.objects.filter(course_id=course_id)
    return queries_temp


def purge_temporary_queries():
    """
    Delete queries made more than TEMPORARY_QUERY_LIFETIME minutes ago along with the saved students from those queries
    Subsequently delete orphaned students in StudentForQuery
    """
    minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=TEMPORARY_QUERY_LIFETIME)
    old_queries = TemporaryQuery.objects.filter(created__lt=minutes_ago)
    saved_students = StudentsForQuery.objects.exclude(query_id__in=old_queries.values_list(DatabaseFields.ID))
    saved_students.delete()
    old_queries.delete()


def make_total_query(course_id, existing_queries):
    """
    Given individual queries that have already been made , aggregate students associated with those queries
    """
    aggregate_existing = set()
    if len(existing_queries) != 0:
        queryset = make_existing_query(course_id, existing_queries).values_list(
            DatabaseFields.ID,
            DatabaseFields.EMAIL,
            DatabaseFields.PROFILE_NAME,
        ).distinct()
        for row in queryset:
            aggregate_existing.add((row[0], row[1], row[2]))
    return aggregate_existing


def make_existing_query(course_id, existing_queries):
    """
    Aggregates single queries in a group into one unified set of students
    """

    if existing_queries is None or len(existing_queries) == 0:
        return None

    ids_in_course = CourseEnrollment.objects.filter(course_id=course_id,
                                                    is_active=1,
                                                    ).values_list(DatabaseFields.USER_ID)
    query = User.objects.filter(id__in=ids_in_course)
    query_dct = defaultdict(list)

    for existing_query in existing_queries:
        if existing_query == "" or existing_query == QueryStatus.WORKING:
            continue
        inclusion_type = TemporaryQuery.objects.filter(id=existing_query)
        filtered_query = StudentsForQuery.objects.filter(query_id=existing_query).values_list(
            DatabaseFields.STUDENT_ID,
            flat=True,
        )
        if inclusion_type.exists():
            query_dct[inclusion_type[0].inclusion].append(filtered_query)

    for not_query in query_dct[INCLUSION_MAP.get(Inclusion.NOT)]:
        query = query.exclude(id__in=not_query)

    for and_query in query_dct[INCLUSION_MAP.get(Inclusion.AND)]:
        query = query.filter(id__in=and_query)

    or_query = User.objects.filter(id__in=ids_in_course)
    qobjs = Q()
    for orq in query_dct[INCLUSION_MAP.get(Inclusion.OR)]:
        qobjs = qobjs | (Q(id__in=orq))

    # if there are only or queries, return the or_query
    if len(query_dct[INCLUSION_MAP.get(Inclusion.NOT)]) == 0 and len(query_dct[INCLUSION_MAP.get(Inclusion.AND)]) == 0:
        return or_query.filter(qobjs)
    # if there is no or_query, do not include it as it contains all the students in the course
    elif len(query_dct[INCLUSION_MAP.get(Inclusion.OR)]) == 0:
        return query
    else:
        return query | or_query.filter(qobjs)
