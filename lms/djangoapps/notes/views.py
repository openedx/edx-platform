from django.contrib.auth.decorators import login_required
from django.http import Http404

from openedx.core.djangoapps.course_views.course_views import CourseViewType
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from notes.models import Note
from notes.utils import notes_enabled_for_course
from xmodule.annotator_token import retrieve_token
from django.utils.translation import ugettext as _


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
        'default_tab': 'myNotes',
    }

    return render_to_response('notes.html', context)


class NotesCourseViewType(CourseViewType):
    """
    A tab for the course notes.
    """
    name = 'notes'
    title = _("My Notes")
    view_name = "notes"

    @classmethod
    def is_enabled(cls, course, settings, user=None):
        if "notes" not in course.advanced_modules:
            return False
        return settings.FEATURES.get('ENABLE_STUDENT_NOTES') and (user is None or user.is_authenticated())
