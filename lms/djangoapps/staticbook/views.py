from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

from courseware.access import has_access
from courseware.courses import get_course_with_access
from lxml import etree

@login_required
def index(request, course_id, page=0):
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    # TODO: This will need to come from S3
    raw_table_of_contents = open('lms/templates/book_toc.xml', 'r')
    table_of_contents = etree.parse(raw_table_of_contents).getroot()

    return render_to_response('staticbook.html',
                              {'page': int(page), 'course': course,
                               'table_of_contents': table_of_contents,
                               'staff_access': staff_access})


def index_shifted(request, course_id, page):
    return index(request, course_id=course_id, page=int(page) + 24)
