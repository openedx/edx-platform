# Grading Views

import logging
import urllib

from django.conf import settings
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from student.models import unique_id_for_user
from courseware.courses import get_course_with_access 

from peer_grading_service import PeerGradingService
from peer_grading_service import MockPeerGradingService
from grading_service import GradingServiceError
import json
from .staff_grading import StaffGrading


log = logging.getLogger(__name__)

template_imports = {'urllib': urllib}
if settings.MOCK_PEER_GRADING:
    peer_gs = MockPeerGradingService() 
else:
    peer_gs = PeerGradingService(settings.PEER_GRADING_INTERFACE)

"""
Reverses the URL from the name and the course id, and then adds a trailing slash if
it does not exist yet

"""
def _reverse_with_slash(url_name, course_id):
    ajax_url = reverse(url_name, kwargs={'course_id': course_id})
    if not ajax_url.endswith('/'):
        ajax_url += '/'
    return ajax_url


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def staff_grading(request, course_id):
    """
    Show the instructor grading interface.
    """
    course = get_course_with_access(request.user, course_id, 'staff')

    ajax_url = _reverse_with_slash('staff_grading', course_id)
        
    return render_to_response('instructor/staff_grading.html', {
        'course': course,
        'course_id': course_id,
        'ajax_url': ajax_url,
        # Checked above
        'staff_access': True, })


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def peer_grading(request, course_id):
    '''
    Show a peer grading interface
    '''
    course = get_course_with_access(request.user, course_id, 'load')

    # call problem list service
    success = False
    error_text = ""
    problem_list = []
    try:
        problem_list_json = peer_gs.get_problem_list(course_id, unique_id_for_user(request.user))
        problem_list_dict = json.loads(problem_list_json)
        success = problem_list_dict['success']
        if 'error' in problem_list_dict:
            error_text = problem_list_dict['error']

        problem_list = problem_list_dict['problem_list']

    except GradingServiceError:
        error_text = "Error occured while contacting the grading service"
        success = False
    # catch error if if the json loads fails
    except ValueError:
        error_text = "Could not get problem list"
        success = False

    ajax_url = _reverse_with_slash('peer_grading', course_id)

    return render_to_response('peer_grading/peer_grading.html', { 
        'course': course,
        'course_id': course_id,
        'ajax_url': ajax_url,
        'success': success,
        'problem_list': problem_list,
        'error_text': error_text,
        # Checked above
        'staff_access': False, })
    

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def peer_grading_problem(request, course_id):
    '''
    Show individual problem interface
    '''
    course = get_course_with_access(request.user, course_id, 'load')
    problem_location = request.GET.get("location")

    ajax_url = _reverse_with_slash('peer_grading', course_id)

    return render_to_response('peer_grading/peer_grading_problem.html', { 
        'view_html': '',
        'course': course,
        'problem_location': problem_location,
        'course_id': course_id,
        'ajax_url': ajax_url,
        # Checked above
        'staff_access': False, })
    

