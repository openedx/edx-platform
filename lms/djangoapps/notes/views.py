from django.http import HttpResponse
from notes.models import Note
import datetime
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
    now = datetime.datetime.now()
    html = "<html><body>It is now %s. Course_id: %s</body></html>" % (now, course_id)
    return HttpResponse(html)
