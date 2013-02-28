# Create your views here.
import json
from datetime import datetime
from django.http import Http404
from mitxmako.shortcuts import render_to_response

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from django.contrib.auth.models import User


def dictfetchall(cursor):
    '''Returns a list of all rows from a cursor as a column: result dict.
    Borrowed from Django documentation'''
    desc = cursor.description
    table=[]
    table.append([col[0] for col in desc])
    table = table + cursor.fetchall()
    print "Table: " + str(table)
    return table

def SQL_query_to_list(cursor, query_string):
    cursor.execute(query_string)
    raw_result=dictfetchall(cursor)
    print raw_result
    return raw_result


def dashboard(request):
    """
    Slightly less hackish hack to show staff enrollment numbers and other
    simple queries.  

    All queries here should be indexed and simple.  Mostly, this means don't
    touch courseware_studentmodule, as tempting as it may be.

    """
    if not request.user.is_staff:
        raise Http404

    # results are passed to the template.  The template knows how to render
    # two types of results: scalars and tables.  Scalars should be represented
    # as "Visible Title": Value and tables should be lists of lists where each
    # inner list represents a single row of the table
    results = {"scalars":{},"tables":{}}

    # count how many users we have
    results["scalars"]["Unique Usernames"]=User.objects.filter().count()
    results["scalars"]["Activated Usernames"]=User.objects.filter(is_active=1).count()
    
    # count how many enrollments we have
    results["scalars"]["Total Enrollments Across All Courses"]=CourseEnrollment.objects.count()

    # establish a direct connection to the database (for executing raw SQL)
    from django.db import connection
    cursor = connection.cursor()

    # define the queries that will generate our user-facing tables
    # table queries need not take the form of raw SQL, but do in this case since
    # the MySQL backend for django isn't very friendly with group by or distinct
    table_queries = {}
    table_queries["course enrollments"]="select count(user_id) as students, course_id from student_courseenrollment group by course_id order by students desc;"
    table_queries["number of students in each number of classes"]="select registrations, count(registrations) from (select count(user_id) as registrations from student_courseenrollment group by user_id) as registrations_per_user group by registrations;"

    # add the result for each of the table_queries to the results object
    for query in table_queries.keys():
        cursor.execute(table_queries[query])
        results["tables"][query] = SQL_query_to_list(cursor, table_queries[query])

    context={"results":results}

    return render_to_response("admin_dashboard.html",context)
