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
from controller_query_service import ControllerQueryService
from grading_service import GradingServiceError
import json
from .staff_grading import StaffGrading
from student.models import unique_id_for_user

import open_ended_util
import open_ended_notifications

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import search

log = logging.getLogger(__name__)

template_imports = {'urllib': urllib}
if settings.MOCK_PEER_GRADING:
    peer_gs = MockPeerGradingService() 
else:
    peer_gs = PeerGradingService(settings.PEER_GRADING_INTERFACE)

controller_url = open_ended_util.get_controller_url()
controller_qs = ControllerQueryService(controller_url)

"""
Reverses the URL from the name and the course id, and then adds a trailing slash if
it does not exist yet

"""
def _reverse_with_slash(url_name, course_id):
    ajax_url = _reverse_without_slash(url_name, course_id)
    if not ajax_url.endswith('/'):
        ajax_url += '/'
    return ajax_url

def _reverse_without_slash(url_name, course_id):
    ajax_url = reverse(url_name, kwargs={'course_id': course_id})
    return ajax_url

DESCRIPTION_DICT = {
            'Peer Grading': "View all problems that require peer assessment in this particular course.",
            'Staff Grading': "View ungraded submissions submitted by students for the open ended problems in the course.",
            'Problems you have submitted': "View open ended problems that you have previously submitted for grading." 
    }
ALERT_DICT = {
            'Peer Grading': "New submissions to grade",
            'Staff Grading': "New submissions to grade",
            'Problems you have submitted': "New grades have been returned" 
    }
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

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def student_problem_list(request, course_id):
    '''
    Show a student problem list
    '''
    course = get_course_with_access(request.user, course_id, 'load')
    student_id = unique_id_for_user(request.user)

    # call problem list service
    success = False
    error_text = ""
    problem_list = []
    base_course_url  = reverse('courses')

    try:
        problem_list_json = controller_qs.get_grading_status_list(course_id, unique_id_for_user(request.user))
        problem_list_dict = json.loads(problem_list_json)
        success = problem_list_dict['success']
        if 'error' in problem_list_dict:
            error_text = problem_list_dict['error']

        problem_list = problem_list_dict['problem_list']

        for i in xrange(0,len(problem_list)):
            problem_url_parts = search.path_to_location(modulestore(), course.id, problem_list[i]['location'])
            problem_url = base_course_url + "/"
            for z in xrange(0,len(problem_url_parts)):
                part = problem_url_parts[z]
                if part is not None:
                    if z==1:
                        problem_url += "courseware/"
                    problem_url += part + "/"

            problem_list[i].update({'actual_url' : problem_url})

    except GradingServiceError:
        error_text = "Error occured while contacting the grading service"
        success = False
    # catch error if if the json loads fails
    except ValueError:
        error_text = "Could not get problem list"
        success = False

    ajax_url = _reverse_with_slash('open_ended_problems', course_id)

    return render_to_response('open_ended_problems/open_ended_problems.html', {
        'course': course,
        'course_id': course_id,
        'ajax_url': ajax_url,
        'success': success,
        'problem_list': problem_list,
        'error_text': error_text,
        # Checked above
        'staff_access': False, })

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def combined_notifications(request, course_id):
    course = get_course_with_access(request.user, course_id, 'load')
    user = request.user
    notifications = open_ended_notifications.combined_notifications(course, user)
    log.debug(notifications)
    response = notifications['response']
    notification_tuples=open_ended_notifications.NOTIFICATION_TYPES

    notification_list = []
    for response_num in xrange(0,len(notification_tuples)):
        tag=notification_tuples[response_num][0]
        if tag in response:
            url_name = notification_tuples[response_num][1]
            human_name = notification_tuples[response_num][2]
            url = _reverse_without_slash(url_name, course_id)
            has_img = response[tag]

            # check to make sure we have descriptions and alert messages
            if human_name in DESCRIPTION_DICT:
                description = DESCRIPTION_DICT[human_name]
            else:
                description = ""

            if human_name in ALERT_DICT:
                alert_message = ALERT_DICT[human_name]
            else:
                alert_message = ""
                
            notification_item = {
                'url' : url,
                'name' : human_name,
                'alert' : has_img,
                'description': description,
                'alert_message': alert_message
            }
            notification_list.append(notification_item)

    ajax_url = _reverse_with_slash('open_ended_notifications', course_id)
    combined_dict = {
        'error_text' : "",
        'notification_list' : notification_list,
        'course' : course,
        'success' : True,
        'ajax_url' : ajax_url,
    }

    return render_to_response('open_ended_problems/combined_notifications.html',
        combined_dict
    )
    

