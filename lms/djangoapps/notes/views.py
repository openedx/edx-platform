from mitxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from notes.models import Note
import json
import logging

log = logging.getLogger(__name__)

def notes(request, course_id):
    ''' Displays a student's notes in a course. '''
    course = get_course_with_access(request.user, course_id, 'load')

    notes = Note.objects.filter(course_id=course_id, user=request.user).order_by('-created', 'uri')

    prettyprint = {'sort_keys':True, 'indent':2, 'separators':(',', ': ')}
    json_notes = json.dumps([n.as_dict() for n in notes], **prettyprint)

    context = {
        'course': course,
        'notes': notes,
        'json_notes': json_notes
    }

    return render_to_response('notes.html', context)
