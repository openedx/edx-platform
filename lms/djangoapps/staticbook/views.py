from django.conf import settings
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

from courseware.access import has_access
from courseware.courses import get_course_with_access
from lxml import etree

@login_required
def index(request, course_id, book_index, page=0):
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    textbook = course.textbooks[int(book_index)]
    table_of_contents = textbook.table_of_contents

    book_url = settings.BOOK_URL    

    return render_to_response('staticbook.html',
                              {'page': int(page), 'course': course, 'book_url': book_url,
                               'table_of_contents': table_of_contents,
                               'staff_access': staff_access})

def index_shifted(request, course_id, page):
    return index(request, course_id=course_id, page=int(page) + 24)
