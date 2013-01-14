"""
This module provides views that proxy to the staff grading backend service.
"""

import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys
from grading_service import GradingService
from grading_service import GradingServiceError

from django.conf import settings
from django.http import HttpResponse, Http404

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor
from student.models import unique_id_for_user
from xmodule.x_module import ModuleSystem
from mitxmako.shortcuts import render_to_string
from xmodule.combined_open_ended_rubric import CombinedOpenEndedRubric
from lxml import etree

log = logging.getLogger(__name__)



class MockStaffGradingService(object):
    """
    A simple mockup of a staff grading service, testing.
    """
    def __init__(self):
        self.cnt = 0

    def get_next(self,course_id, location, grader_id):
        self.cnt += 1
        return json.dumps({'success': True,
                           'submission_id': self.cnt,
                           'submission': 'Test submission {cnt}'.format(cnt=self.cnt),
                           'num_graded': 3,
                           'min_for_ml': 5,
                           'num_pending': 4,
                           'prompt': 'This is a fake prompt',
                           'ml_error_info': 'ML info',
                           'max_score': 2 + self.cnt % 3,
                           'rubric': 'A rubric'})

    def get_problem_list(self, course_id, grader_id):
        self.cnt += 1
        return json.dumps({'success': True,
        'problem_list': [
          json.dumps({'location': 'i4x://MITx/3.091x/problem/open_ended_demo1', \
            'problem_name': "Problem 1", 'num_graded': 3, 'num_pending': 5, 'min_for_ml': 10}),
          json.dumps({'location': 'i4x://MITx/3.091x/problem/open_ended_demo2', \
            'problem_name': "Problem 2", 'num_graded': 1, 'num_pending': 5, 'min_for_ml': 10})
        ]})


    def save_grade(self, course_id, grader_id, submission_id, score, feedback, skipped):
        return self.get_next(course_id, 'fake location', grader_id)


class StaffGradingService(GradingService):
    """
    Interface to staff grading backend.
    """
    def __init__(self, config):
        super(StaffGradingService, self).__init__(config)
        self.get_next_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.get_problem_list_url = self.url + '/get_problem_list/'


    def get_problem_list(self, course_id, grader_id):
        """
        Get the list of problems for a given course.

        Args:
            course_id: course id that we want the problems of
            grader_id: who is grading this?  The anonymous user_id of the grader.

        Returns:
            json string with the response from the service.  (Deliberately not
            writing out the fields here--see the docs on the staff_grading view
            in the grading_controller repo)

        Raises:
            GradingServiceError: something went wrong with the connection.
        """
        params = {'course_id': course_id,'grader_id': grader_id}
        return self.get(self.get_problem_list_url, params)


    def get_next(self, course_id, location, grader_id):
        """
        Get the next thing to grade.

        Args:
            course_id: the course that this problem belongs to
            location: location of the problem that we are grading and would like the
                next submission for
            grader_id: who is grading this?  The anonymous user_id of the grader.

        Returns:
            json string with the response from the service.  (Deliberately not
            writing out the fields here--see the docs on the staff_grading view
            in the grading_controller repo)

        Raises:
            GradingServiceError: something went wrong with the connection.
        """
        return self.get(self.get_next_url,
                                      params={'location': location,
                                              'grader_id': grader_id})


    def save_grade(self, course_id, grader_id, submission_id, score, feedback, skipped, rubric_scores):
        """
        Save a score and feedback for a submission.

        Returns:
            json dict with keys
                'success': bool
                'error': error msg, if something went wrong.

        Raises:
            GradingServiceError if there's a problem connecting.
        """
        data = {'course_id': course_id,
                'submission_id': submission_id,
                'score': score,
                'feedback': feedback,
                'grader_id': grader_id,
                'skipped': skipped,
                'rubric_scores': rubric_scores,
                'rubric_scores_complete': True}

        return self.post(self.save_grade_url, data=data)

# don't initialize until staff_grading_service() is called--means that just
# importing this file doesn't create objects that may not have the right config
_service = None

module_system = ModuleSystem("", None, None, render_to_string, None)

def staff_grading_service():
    """
    Return a staff grading service instance--if settings.MOCK_STAFF_GRADING is True,
    returns a mock one, otherwise a real one.

    Caches the result, so changing the setting after the first call to this
    function will have no effect.
    """
    global _service
    if _service is not None:
        return _service

    if settings.MOCK_STAFF_GRADING:
        _service = MockStaffGradingService()
    else:
        _service = StaffGradingService(settings.STAFF_GRADING_INTERFACE)

    return _service

def _err_response(msg):
    """
    Return a HttpResponse with a json dump with success=False, and the given error message.
    """
    return HttpResponse(json.dumps({'success': False, 'error': msg}),
                        mimetype="application/json")


def _check_access(user, course_id):
    """
    Raise 404 if user doesn't have staff access to course_id
    """
    course_location = CourseDescriptor.id_to_location(course_id)
    if not has_access(user, course_location, 'staff'):
        raise Http404

    return


def get_next(request, course_id):
    """
    Get the next thing to grade for course_id and with the location specified
    in the request.

    Returns a json dict with the following keys:

    'success': bool

    'submission_id': a unique identifier for the submission, to be passed back
                     with the grade.

    'submission': the submission, rendered as read-only html for grading

    'rubric': the rubric, also rendered as html.

    'message': if there was no submission available, but nothing went wrong,
            there will be a message field.

    'error': if success is False, will have an error message with more info.
    """
    _check_access(request.user, course_id)

    required = set(['location'])
    if request.method != 'POST':
        raise Http404
    actual = set(request.POST.keys())
    missing = required - actual
    if len(missing) > 0:
        return _err_response('Missing required keys {0}'.format(
            ', '.join(missing)))
    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']

    return HttpResponse(_get_next(course_id, grader_id, location),
                        mimetype="application/json")


def get_problem_list(request, course_id):
    """
    Get all the problems for the given course id

    Returns a json dict with the following keys:
        success: bool

        problem_list: a list containing json dicts with the following keys:
            each dict represents a different problem in the course

            location: the location of the problem

            problem_name: the name of the problem

            num_graded: the number of responses that have been graded

            num_pending: the number of responses that are sitting in the queue

            min_for_ml: the number of responses that need to be graded before
                the ml can be run

    """
    _check_access(request.user, course_id)
    try:
        response = staff_grading_service().get_problem_list(course_id, unique_id_for_user(request.user))
        return HttpResponse(response,
                mimetype="application/json")
    except GradingServiceError:
        log.exception("Error from grading service.  server url: {0}"
                      .format(staff_grading_service().url))
        return HttpResponse(json.dumps({'success': False,
                           'error': 'Could not connect to grading service'}))


def _get_next(course_id, grader_id, location):
    """
    Implementation of get_next (also called from save_grade) -- returns a json string
    """
    try:
        response = staff_grading_service().get_next(course_id, location, grader_id)
        response_json = json.loads(response)
        rubric = response_json['rubric']
        rubric_renderer = CombinedOpenEndedRubric(False)
        success, rubric_html = rubric_renderer.render_rubric(rubric)
        if not success:
            error_message = "Could not render rubric: {0}".format(rubric)
            log.exception(error_message)
            return json.dumps({'success': False,
                               'error': error_message})
        response_json['rubric'] = rubric_html
        return json.dumps(response_json)
    except GradingServiceError:
        log.exception("Error from grading service.  server url: {0}"
                      .format(staff_grading_service().url))
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})
    # if we can't parse the rubric into HTML, 
    except etree.XMLSyntaxError:
        log.exception("Cannot parse rubric string. Raw string: {0}"
                      .format(rubric))
        return json.dumps({'success': False,
                           'error': 'Error displaying submission'})


@expect_json
def save_grade(request, course_id):
    """
    Save the grade and feedback for a submission, and, if all goes well, return
    the next thing to grade.

    Expects the following POST parameters:
    'score': int
    'feedback': string
    'submission_id': int

    Returns the same thing as get_next, except that additional error messages
    are possible if something goes wrong with saving the grade.
    """
    _check_access(request.user, course_id)

    if request.method != 'POST':
        raise Http404

    required = set(['score', 'feedback', 'submission_id', 'location', 'rubric_scores[]'])
    actual = set(request.POST.keys())
    missing = required - actual
    if len(missing) > 0:
        return _err_response('Missing required keys {0}'.format(
            ', '.join(missing)))

    grader_id = unique_id_for_user(request.user)
    p = request.POST


    location = p['location']
    skipped =  'skipped' in p

    try:
        result_json = staff_grading_service().save_grade(course_id,
                                          grader_id,
                                          p['submission_id'],
                                          p['score'],
                                          p['feedback'],
                                          skipped,
                                          p.getlist('rubric_scores[]'))
    except GradingServiceError:
        log.exception("Error saving grade")
        return _err_response('Could not connect to grading service')

    try:
        result = json.loads(result_json)
    except ValueError:
        log.exception("save_grade returned broken json: %s", result_json)
        return _err_response('Grading service returned mal-formatted data.')

    if not result.get('success', False):
        log.warning('Got success=False from grading service.  Response: %s', result_json)
        return _err_response('Grading service failed')

    # Ok, save_grade seemed to work.  Get the next submission to grade.
    return HttpResponse(_get_next(course_id, grader_id, location),
                        mimetype="application/json")

