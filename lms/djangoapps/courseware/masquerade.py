'''
---------------------------------------- Masequerade ----------------------------------------
Allow course staff to see a student or staff view of courseware.
Which kind of view has been selected is stored in the session state.
'''

import json
import logging

from django.http import HttpResponse
from django.conf import settings

log = logging.getLogger(__name__)

MASQ_KEY = 'masquerade_identity'


def handle_ajax(request, marg):
    '''
    Handle ajax call from "staff view" / "student view" toggle button
    '''
    if marg == 'toggle':
        status = request.session.get(MASQ_KEY, '')
        if status is None or status in ['', 'staff']:
            status = 'student'
        else:
            status = 'staff'
        request.session[MASQ_KEY] = status
    return HttpResponse(json.dumps({'status': status}))


def setup_masquerade(request, staff_access=False):
    '''
    Setup masquerade identity (allows staff to view courseware as either staff or student)

    Uses request.session[MASQ_KEY] to store status of masquerading.
    Adds masquerade status to request.user, if masquerading active.
    Return string version of status of view (either 'staff' or 'student')
    '''
    if request.user is None:
        return None

    if not settings.FEATURES.get('ENABLE_MASQUERADE', False):
        return None

    if not staff_access:  # can masquerade only if user has staff access to course
        return None

    usertype = request.session.get(MASQ_KEY, '')
    if usertype is None or not usertype:
        request.session[MASQ_KEY] = 'staff'
        usertype = 'staff'

    if usertype == 'student':
        request.user.masquerade_as_student = True

    return usertype


def is_masquerading_as_student(user):
    '''
    Return True if user is masquerading as a student, False otherwise
    '''
    masq = getattr(user, 'masquerade_as_student', False)
    return masq==True
