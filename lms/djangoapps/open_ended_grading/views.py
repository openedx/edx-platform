# Grading Views

import logging

from django.conf import settings
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from student.models import unique_id_for_user
from courseware.courses import get_course_with_access

from xmodule.x_module import ModuleSystem
from xmodule.open_ended_grading_classes.controller_query_service import ControllerQueryService, convert_seconds_to_human_readable
from xmodule.open_ended_grading_classes.grading_service_module import GradingServiceError
import json
from student.models import unique_id_for_user

import open_ended_notifications

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import search
from xmodule.modulestore.exceptions import ItemNotFoundError

from django.http import HttpResponse, Http404, HttpResponseRedirect
from mitxmako.shortcuts import render_to_string

log = logging.getLogger(__name__)

system = ModuleSystem(
    ajax_url=None,
    track_function=None,
    get_module=None,
    render_template=render_to_string,
    replace_urls=None,
    xblock_model_data={}
)

controller_qs = ControllerQueryService(settings.OPEN_ENDED_GRADING_INTERFACE, system)

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
    'Problems you have submitted': "View open ended problems that you have previously submitted for grading.",
    'Flagged Submissions': "View submissions that have been flagged by students as inappropriate."
}
ALERT_DICT = {
    'Peer Grading': "New submissions to grade",
    'Staff Grading': "New submissions to grade",
    'Problems you have submitted': "New grades have been returned",
    'Flagged Submissions': "Submissions have been flagged for review"
}

STUDENT_ERROR_MESSAGE = "Error occured while contacting the grading service.  Please notify course staff."
STAFF_ERROR_MESSAGE = "Error occured while contacting the grading service.  Please notify the development team.  If you do not have a point of contact, please email Vik at vik@edx.org"


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


def find_peer_grading_module(course):
    """
    Given a course, finds the first peer grading module in it.
    @param course: A course object.
    @return: boolean found_module, string problem_url
    """
    #Reverse the base course url
    base_course_url = reverse('courses')
    found_module = False
    problem_url = ""

    #Get the course id and split it
    course_id_parts = course.id.split("/")
    log.info("COURSE ID PARTS")
    log.info(course_id_parts)
    #Get the peer grading modules currently in the course.  Explicitly specify the course id to avoid issues with different runs.
    items = modulestore().get_items(['i4x', course_id_parts[0], course_id_parts[1], 'peergrading', None],
                                    course_id=course.id)
    #See if any of the modules are centralized modules (ie display info from multiple problems)
    items = [i for i in items if not getattr(i, "use_for_single_location", True)]
    #Get the first one
    if len(items) > 0:
        item_location = items[0].location
        #Generate a url for the first module and redirect the user to it
        problem_url_parts = search.path_to_location(modulestore(), course.id, item_location)
        problem_url = generate_problem_url(problem_url_parts, base_course_url)
        found_module = True

    return found_module, problem_url


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def peer_grading(request, course_id):
    '''
    When a student clicks on the "peer grading" button in the open ended interface, link them to a peer grading
    xmodule in the course.
    '''

    #Get the current course
    course = get_course_with_access(request.user, course_id, 'load')

    found_module, problem_url = find_peer_grading_module(course)
    if not found_module:
        #This is a student_facing_error
        error_message = """
        Error with initializing peer grading.
        There has not been a peer grading module created in the courseware that would allow you to grade others.
        Please check back later for this.
        """
        #This is a dev_facing_error
        log.exception(error_message + "Current course is: {0}".format(course_id))
        return HttpResponse(error_message)

    return HttpResponseRedirect(problem_url)


def generate_problem_url(problem_url_parts, base_course_url):
    """
    From a list of problem url parts generated by search.path_to_location and a base course url, generates a url to a problem
    @param problem_url_parts: Output of search.path_to_location
    @param base_course_url: Base url of a given course
    @return: A path to the problem
    """
    problem_url = base_course_url + "/"
    for z in xrange(0, len(problem_url_parts)):
        part = problem_url_parts[z]
        if part is not None:
            if z == 1:
                problem_url += "courseware/"
            problem_url += part + "/"
    return problem_url


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def student_problem_list(request, course_id):
    '''
    Show a student problem list to a student.  Fetch the list from the grading controller server, get some metadata,
    and then show it to the student.
    '''
    course = get_course_with_access(request.user, course_id, 'load')
    student_id = unique_id_for_user(request.user)

    # call problem list service
    success = False
    error_text = ""
    problem_list = []
    base_course_url = reverse('courses')

    try:
        #Get list of all open ended problems that the grading server knows about
        problem_list_json = controller_qs.get_grading_status_list(course_id, unique_id_for_user(request.user))
        problem_list_dict = json.loads(problem_list_json)
        success = problem_list_dict['success']
        if 'error' in problem_list_dict:
            error_text = problem_list_dict['error']
            problem_list = []
        else:
            problem_list = problem_list_dict['problem_list']

        #A list of problems to remove (problems that can't be found in the course)
        list_to_remove = []
        for i in xrange(0, len(problem_list)):
            try:
                #Try to load each problem in the courseware to get links to them
                problem_url_parts = search.path_to_location(modulestore(), course.id, problem_list[i]['location'])
            except ItemNotFoundError:
                #If the problem cannot be found at the location received from the grading controller server, it has been deleted by the course author.
                #Continue with the rest of the location to construct the list
                error_message = "Could not find module for course {0} at location {1}".format(course.id,
                                                                                              problem_list[i][
                                                                                                  'location'])
                log.error(error_message)
                #Mark the problem for removal from the list
                list_to_remove.append(i)
                continue
            problem_url = generate_problem_url(problem_url_parts, base_course_url)
            problem_list[i].update({'actual_url': problem_url})
            eta_available = problem_list[i]['eta_available']
            if isinstance(eta_available, basestring):
                eta_available = (eta_available.lower() == "true")

            eta_string = "N/A"
            if eta_available:
                try:
                    eta_string = convert_seconds_to_human_readable(int(problem_list[i]['eta']))
                except:
                    #This is a student_facing_error
                    eta_string = "Error getting ETA."
            problem_list[i].update({'eta_string': eta_string})

    except GradingServiceError:
        #This is a student_facing_error
        error_text = STUDENT_ERROR_MESSAGE
        #This is a dev facing error
        log.error("Problem contacting open ended grading service.")
        success = False
    # catch error if if the json loads fails
    except ValueError:
        #This is a student facing error
        error_text = STUDENT_ERROR_MESSAGE
        #This is a dev_facing_error
        log.error("Problem with results from external grading service for open ended.")
        success = False

    #Remove problems that cannot be found in the courseware from the list
    problem_list = [problem_list[i] for i in xrange(0, len(problem_list)) if i not in list_to_remove]
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
def flagged_problem_list(request, course_id):
    '''
    Show a student problem list
    '''
    course = get_course_with_access(request.user, course_id, 'staff')
    student_id = unique_id_for_user(request.user)

    # call problem list service
    success = False
    error_text = ""
    problem_list = []
    base_course_url = reverse('courses')

    try:
        problem_list_json = controller_qs.get_flagged_problem_list(course_id)
        problem_list_dict = json.loads(problem_list_json)
        success = problem_list_dict['success']
        if 'error' in problem_list_dict:
            error_text = problem_list_dict['error']
            problem_list = []
        else:
            problem_list = problem_list_dict['flagged_submissions']

    except GradingServiceError:
        #This is a staff_facing_error
        error_text = STAFF_ERROR_MESSAGE
        #This is a dev_facing_error
        log.error("Could not get flagged problem list from external grading service for open ended.")
        success = False
    # catch error if if the json loads fails
    except ValueError:
        #This is a staff_facing_error
        error_text = STAFF_ERROR_MESSAGE
        #This is a dev_facing_error
        log.error("Could not parse problem list from external grading service response.")
        success = False

    ajax_url = _reverse_with_slash('open_ended_flagged_problems', course_id)
    context = {
        'course': course,
        'course_id': course_id,
        'ajax_url': ajax_url,
        'success': success,
        'problem_list': problem_list,
        'error_text': error_text,
        # Checked above
        'staff_access': True,
    }
    return render_to_response('open_ended_problems/open_ended_flagged_problems.html', context)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def combined_notifications(request, course_id):
    """
    Gets combined notifications from the grading controller and displays them
    """
    course = get_course_with_access(request.user, course_id, 'load')
    user = request.user
    notifications = open_ended_notifications.combined_notifications(course, user)
    response = notifications['response']
    notification_tuples = open_ended_notifications.NOTIFICATION_TYPES

    notification_list = []
    for response_num in xrange(0, len(notification_tuples)):
        tag = notification_tuples[response_num][0]
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
                'url': url,
                'name': human_name,
                'alert': has_img,
                'description': description,
                'alert_message': alert_message
            }
            #The open ended panel will need to link the "peer grading" button in the panel to a peer grading
            #xmodule defined in the course.  This checks to see if the human name of the server notification
            #that we are currently processing is "peer grading".  If it is, it looks for a peer grading
            #module in the course.  If none exists, it removes the peer grading item from the panel.
            if human_name == "Peer Grading":
                found_module, problem_url = find_peer_grading_module(course)
                if found_module:
                    notification_list.append(notification_item)
            else:
                notification_list.append(notification_item)

    ajax_url = _reverse_with_slash('open_ended_notifications', course_id)
    combined_dict = {
        'error_text': "",
        'notification_list': notification_list,
        'course': course,
        'success': True,
        'ajax_url': ajax_url,
    }

    return render_to_response('open_ended_problems/combined_notifications.html', combined_dict)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def take_action_on_flags(request, course_id):
    """
    Takes action on student flagged submissions.
    Currently, only support unflag and ban actions.
    """
    if request.method != 'POST':
        raise Http404

    required = ['submission_id', 'action_type', 'student_id']
    for key in required:
        if key not in request.POST:
            #This is a staff_facing_error
            return HttpResponse(json.dumps({'success': False,
                                            'error': STAFF_ERROR_MESSAGE + 'Missing key {0} from submission.  Please reload and try again.'.format(
                                                key)}),
                                mimetype="application/json")

    p = request.POST
    submission_id = p['submission_id']
    action_type = p['action_type']
    student_id = p['student_id']
    student_id = student_id.strip(' \t\n\r')
    submission_id = submission_id.strip(' \t\n\r')
    action_type = action_type.lower().strip(' \t\n\r')
    try:
        response = controller_qs.take_action_on_flags(course_id, student_id, submission_id, action_type)
        return HttpResponse(response, mimetype="application/json")
    except GradingServiceError:
        #This is a dev_facing_error
        log.exception(
            "Error taking action on flagged peer grading submissions, submission_id: {0}, action_type: {1}, grader_id: {2}".format(
                submission_id, action_type, grader_id))
        return _err_response(STAFF_ERROR_MESSAGE)
