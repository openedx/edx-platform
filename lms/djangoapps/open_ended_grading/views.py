# Grading Views

from collections import defaultdict
import csv
import logging
import os
import urllib

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from courseware import grades
from courseware.access import has_access, get_access_group_name
from courseware.courses import get_course_with_access 
from django_comment_client.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from django_comment_client.utils import has_forum_access
from psychometrics import psychoanalyze
from student.models import CourseEnrollment
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
import track.views

from .staff_grading import StaffGrading


log = logging.getLogger(__name__)

template_imports = {'urllib': urllib}
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def staff_grading(request, course_id):
    """
    Show the instructor grading interface.
    """
    course = get_course_with_access(request.user, course_id, 'staff')

    grading = StaffGrading(course)

    ajax_url = reverse('staff_grading', kwargs={'course_id': course_id})
    if not ajax_url.endswith('/'):
        ajax_url += '/'
        
    return render_to_response('instructor/staff_grading.html', {
        'view_html': grading.get_html(),
        'course': course,
        'course_id': course_id,
        'ajax_url': ajax_url,
        # Checked above
        'staff_access': True, })

