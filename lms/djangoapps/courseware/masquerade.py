#---------------------------------------- Masequerade ----------------------------------------
#
# Allow course staff to see a student or staff view of courseware.
# Which kind of view has been selected is stored in the session state.

import json
import logging
import urllib

from functools import partial

from django.conf import settings
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
#from django.views.decorators.csrf import ensure_csrf_cookie
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from django.http import HttpResponse

from courseware import grades
from courseware.access import has_access
from courseware.courses import (get_courses, get_course_with_access,
                                get_courses_by_university, sort_by_announcement)
import courseware.tabs as tabs
from courseware.models import StudentModuleCache
from module_render import toc_for_course, get_module, get_instance_module, get_module_for_descriptor

from django_comment_client.utils import get_discussion_title

from student.models import UserTestGroup, CourseEnrollment
from util.cache import cache, cache_if_anonymous
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location

log = logging.getLogger(__name__)

def handle_ajax(request, marg):
    log.debug('masquerade handle_ajax marg=%s' % marg)
    return HttpResponse(json.dumps({}))


MASQ_VAR = 'masquerade_identity'

class Masquerade(object):
    '''
    Manage masquerade identity (allows staff to view courseware as either staff or student)

    State variables:

    actual_user = User instance of the real, un-masqueraded user
    user = User instance (what actual user is masquerading as)
    usertype = "staff" or "student" or "nonstaff"
    
    '''

    def __init__(self, request, staff_access=False):
        '''
        request = Django http request object
        '''
        self.request = request
        self.actual_user = request.user
        self.user = request.user
        self.usertype = "nonstaff"
        if request.user is not None and staff_access:
            self.usertype = request.session.get(MASQ_VAR,'staff')
            if self.usertype=='student':
                self.user = self.get_student_user()
                    
    def get_student_user(self):
        '''
        Each staff user can have a corresponding student identity, with
        the same username + "__student".  Return that User.
        Create the student user if doesn't already exist.
        '''
        suffix = '__student'
        if self.user.username.endswith(suffix):
            return self.user
        user = User.get_or_create(username=self.user+suffix, email=self.user.email)
        profile = UserProfile.get_or_create(user=user, name=self.user.profile.name+suffix)
        return user

    def toggle_status(self):
        """
        Toggle status from staff from student
        """
        if self.usertype=='student':
            self.user = self.actual_user
        elif self.usertype=='staff':
            self.user = self.get_student_user()

    def view_status(self):
        '''
        Return string version of status of view
        '''
        STAT = {'staff': '<font color="red">Staff view</font>', 'student': '<font color="orange">Student view</font>'}
        return STAT.get(self.usertype,'')
