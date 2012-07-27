# Create your views here.
import json
from datetime import datetime
from django.http import HttpResponse, Http404

def dictfetchall(cursor):
    '''Returns all rows from a cursor as a dict.
    Borrowed from Django documentation'''
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

def dashboard(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up
    """
    if not request.user.is_staff:
        raise Http404

    query = "select count(user_id) as students, course_id from student_courseenrollment group by course_id order by students desc"

    from django.db import connection
    cursor = connection.cursor()
    results = dictfetchall(cursor.execute(query))
    

    return HttpResponse(json.dumps(results, indent=4))
