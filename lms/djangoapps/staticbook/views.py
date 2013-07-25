"""
Views for serving static textbooks.
"""

from django.contrib.auth.decorators import login_required
from django.http import Http404
from mitxmako.shortcuts import render_to_response

from courseware.access import has_access
from courseware.courses import get_course_with_access
from notes.utils import notes_enabled_for_course
from static_replace import replace_static_urls


@login_required
def index(request, course_id, book_index, page=None):
    """
    Serve static image-based textbooks.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.textbooks[book_index]
    table_of_contents = textbook.table_of_contents

    if page is None:
        page = textbook.start_page

    return render_to_response(
        'staticbook.html',
        {
            'book_index': book_index, 'page': int(page),
            'course': course,
            'book_url': textbook.book_url,
            'table_of_contents': table_of_contents,
            'start_page': textbook.start_page,
            'end_page': textbook.end_page,
            'staff_access': staff_access,
        },
    )


def remap_static_url(original_url, course):
    """Remap a URL in the ways the course requires."""
    # Ick: this should be possible without having to quote and unquote the URL...
    input_url = "'" + original_url + "'"
    output_url = replace_static_urls(
        input_url,
        getattr(course, 'data_dir', None),
        coures_id=course.location.course_id,
    )
    # strip off the quotes again...
    return output_url[1:-1]


@login_required
def pdf_index(request, course_id, book_index, chapter=None, page=None):
    """
    Display a PDF textbook.

    course_id: course for which to display text.  The course should have
      "pdf_textbooks" property defined.

    book index:  zero-based index of which PDF textbook to display.

    chapter:  (optional) one-based index into the chapter array of textbook PDFs to display.
        Defaults to first chapter.  Specifying this assumes that there are separate PDFs for
        each chapter in a textbook.

    page:  (optional) one-based page number to display within the PDF.  Defaults to first page.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.pdf_textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.pdf_textbooks[book_index]

    if 'url' in textbook:
        textbook['url'] = remap_static_url(textbook['url'], course)
    # then remap all the chapter URLs as well, if they are provided.
    if 'chapters' in textbook:
        for entry in textbook['chapters']:
            entry['url'] = remap_static_url(entry['url'], course)

    return render_to_response(
        'static_pdfbook.html',
        {
            'book_index': book_index,
            'course': course,
            'textbook': textbook,
            'chapter': chapter,
            'page': page,
            'staff_access': staff_access,
        },
    )


@login_required
def html_index(request, course_id, book_index, chapter=None):
    """
    Display an HTML textbook.

    course_id: course for which to display text.  The course should have
      "html_textbooks" property defined.

    book index:  zero-based index of which HTML textbook to display.

    chapter:  (optional) one-based index into the chapter array of textbook HTML files to display.
        Defaults to first chapter.  Specifying this assumes that there are separate HTML files for
        each chapter in a textbook.
    """
    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')
    notes_enabled = notes_enabled_for_course(course)

    book_index = int(book_index)
    if book_index < 0 or book_index >= len(course.html_textbooks):
        raise Http404("Invalid book index value: {0}".format(book_index))
    textbook = course.html_textbooks[book_index]

    if 'url' in textbook:
        textbook['url'] = remap_static_url(textbook['url'], course)
    # then remap all the chapter URLs as well, if they are provided.
    if 'chapters' in textbook:
        for entry in textbook['chapters']:
            entry['url'] = remap_static_url(entry['url'], course)

    return render_to_response(
        'static_htmlbook.html',
        {
            'book_index': book_index,
            'course': course,
            'textbook': textbook,
            'chapter': chapter,
            'staff_access': staff_access,
            'notes_enabled': notes_enabled,
        },
    )
