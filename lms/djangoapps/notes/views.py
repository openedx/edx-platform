from mitxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from notes.models import Note
import json
import logging

log = logging.getLogger(__name__)

#----------------------------------------------------------------------#
# HTML views.
#
# Example for enabling annotator.js (snippet):
#
# $('body').annotator()
#   .annotator('addPlugin', 'Tags')
#   .annotator('addPlugin', 'Store', { 'prefix': '/courses/HarvardX/CB22x/2013_Spring/notes/api' });
#
# See annotator.js docs:
#
#   https://github.com/okfn/annotator/wiki

def notes(request, course_id):
    course = get_course_with_access(request.user, course_id, 'load')

    notes = Note.objects.filter(user_id=request.user.id)
    prettyprint = {'sort_keys':True, 'indent':2, 'separators':(',', ': ')}
    json_notes = json.dumps([n.as_dict() for n in notes], **prettyprint)

    context = {
        'course': course,
        'notes': notes,
        'json_notes': json_notes
    }

    return render_to_response('notes.html', context)
