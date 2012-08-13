from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

from courseware.courses import check_course
from lxml import etree

@login_required
def index(request, course_id, page=0):
    course = check_course(request.user, course_id)
    raw_table_of_contents = open('lms/templates/book_toc.xml', 'r') # TODO: This will need to come from S3
    table_of_contents = etree.parse(raw_table_of_contents).getroot()
    return render_to_response('staticbook.html', {'page': int(page), 'course': course, 'table_of_contents': table_of_contents})


def index_shifted(request, course_id, page):
    return index(request, course_id=course_id, page=int(page) + 24)
