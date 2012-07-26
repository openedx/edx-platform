from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

from courseware.courses import check_course


@login_required
def index(request, course_id, page=0):
    course = check_course(course_id)
    return render_to_response('staticbook.html', {'page': int(page), 'course': course})


def index_shifted(request, course_id, page):
    return index(request, course_id=course_id, page=int(page) + 24)
