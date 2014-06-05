from django.contrib.auth.decorators import login_required
from django.http import Http404
from edxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from notes.models import Note
from notes.utils import notes_enabled_for_course
from xmodule.annotator_token import retrieve_token


@login_required
def notes(request, course_id):
    ''' Displays the student's notes. '''

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)
    if not notes_enabled_for_course(course):
        raise Http404

    notes = Note.objects.filter(course_id=course_key, user=request.user).order_by('-created', 'uri')

    student = request.user
    storage = course.annotation_storage_url
    context = {
        'course': course,
        'notes': notes,
        'student': student,
        'storage': storage,
        'token': retrieve_token(student.email, course.annotation_token_secret),
    }

    return render_to_response('notes.html', context)
