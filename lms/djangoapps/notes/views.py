import datetime
from django.contrib.auth.decorators import login_required
from django.http import (Http404, HttpResponse)
from edxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from notes.models import Note
from notes.utils import notes_enabled_for_course
from xmodule.firebase_token_generator import create_token

@login_required
def notes(request, course_id):
    ''' Displays the student's notes. '''

    course = get_course_with_access(request.user, course_id, 'load')
    if not notes_enabled_for_course(course):
        raise Http404

    notes = Note.objects.filter(course_id=course_id, user=request.user).order_by('-created', 'uri')

    def token(userId):
        '''
        Return a token for the backend of annotations.
        It uses the course id to retrieve a variable that contains the secret
        token found in inheritance.py. It also contains information of when
        the token was issued. This will be stored with the user along with
        the id for identification purposes in the backend.
        '''
        dtnow = datetime.datetime.now()
        dtutcnow = datetime.datetime.utcnow()
        delta = dtnow - dtutcnow
        newhour, newmin = divmod((delta.days * 24 * 60 * 60 + delta.seconds + 30) // 60, 60)
        newtime = "%s%+02d:%02d" % (dtnow.isoformat(), newhour, newmin)
        if "annotation_token_secret" in dir(course):
            secret = course.annotation_token_secret
        else:
            secret = "NoKeyFound"
        custom_data = {"issuedAt": newtime, "consumerKey": secret, "userId": userId, "ttl": 86400}
        newtoken = create_token(secret, custom_data)
        return newtoken

    student = request.user
    storage = course.annotation_storage_url
    context = {
        'course': course,
        'notes': notes,
        'student': student,
        'storage': storage,
        'token': token(student.email)
    }
    return render_to_response('notes.html', context)
