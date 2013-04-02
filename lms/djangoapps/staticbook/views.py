from lxml import etree

from django.contrib.auth.decorators import login_required
from django.http import Http404
from mitxmako.shortcuts import render_to_response

from courseware.access import has_access
from courseware.courses import get_course_with_access
from static_replace import replace_static_urls


@login_required
def index(request, course_id, book_index, page=None):
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.textbooks[book_index]
    table_of_contents = textbook.table_of_contents

    if page is None:
        page = textbook.start_page

    return render_to_response('staticbook.html',
                              {'book_index': book_index, 'page': int(page),
                               'course': course, 'book_url': textbook.book_url,
                               'table_of_contents': table_of_contents,
                               'start_page': textbook.start_page,
                               'end_page': textbook.end_page,
                               'staff_access': staff_access})


def index_shifted(request, course_id, page):
    return index(request, course_id=course_id, page=int(page) + 24)


@login_required
def pdf_index(request, course_id, book_index, chapter=None, page=None):
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.pdf_textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.pdf_textbooks[book_index]

    def remap_static_url(original_url, course):
        input_url = "'" + original_url + "'"
        output_url = replace_static_urls(
                    input_url,
                    getattr(course, 'data_dir', None),
                    course_namespace=course.location
                )
        # strip off the quotes again...
        return output_url[1:-1]

    if 'url' in textbook:
        textbook['url'] = remap_static_url(textbook['url'], course)
    # then remap all the chapter URLs as well, if they are provided.
    if 'chapters' in textbook:
        for entry in textbook['chapters']:
            entry['url'] = remap_static_url(entry['url'], course)


    return render_to_response('static_pdfbook.html',
                              {'book_index': book_index,
                               'course': course,
                               'textbook': textbook,
                               'chapter': chapter,
                               'page': page,
                               'staff_access': staff_access})

@login_required
def html_index(request, course_id, book_index, chapter=None, anchor_id=None):
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.html_textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.html_textbooks[book_index]

    def remap_static_url(original_url, course):
        input_url = "'" + original_url + "'"
        output_url = replace_static_urls(
                    input_url,
                    getattr(course, 'data_dir', None),
                    course_namespace=course.location
                )
        # strip off the quotes again...
        return output_url[1:-1]

    if 'url' in textbook:
        textbook['url'] = remap_static_url(textbook['url'], course)
    # then remap all the chapter URLs as well, if they are provided.
    if 'chapters' in textbook:
        for entry in textbook['chapters']:
            entry['url'] = remap_static_url(entry['url'], course)


    return render_to_response('static_htmlbook.html',
                              {'book_index': book_index,
                               'course': course,
                               'textbook': textbook,
                               'chapter': chapter,
                               'anchor_id': anchor_id,
                               'staff_access': staff_access})
