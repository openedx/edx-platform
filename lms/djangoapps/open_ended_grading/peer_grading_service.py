"""
This module provides an interface on the grading-service backend
for peer grading

Use peer_grading_service() to get the version specified
in settings.PEER_GRADING_INTERFACE

"""
import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

from django.conf import settings
from django.http import HttpResponse, Http404
from grading_service import GradingService
from grading_service import GradingServiceError

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor
from student.models import unique_id_for_user

log = logging.getLogger(__name__)

"""
This is a mock peer grading service that can be used for unit tests
without making actual service calls to the grading controller
"""
class MockPeerGradingService(object):
    def get_next_submission(self, problem_location, grader_id):
        return json.dumps({'success': True,
                'submission_id':1,
                'submission_key': "",
                'student_response': 'fake student response',
                'prompt': 'fake submission prompt',
                'rubric': 'fake rubric',
                'max_score': 4})

    def save_grade(self, location, grader_id, submission_id, 
            score, feedback, submission_key):
        return json.dumps({'success': True})

    def is_student_calibrated(self, problem_location, grader_id):
        return json.dumps({'success': True, 'calibrated': True})
    
    def show_calibration_essay(self, problem_location, grader_id):
        return json.dumps({'success': True,
                'submission_id':1,
                'submission_key': '',
                'student_response': 'fake student response',
                'prompt': 'fake submission prompt',
                'rubric': 'fake rubric',
                'max_score': 4})

    def save_calibration_essay(self, problem_location, grader_id, 
            calibration_essay_id, submission_key, score, feedback):
        return {'success': True, 'actual_score': 2}

    def get_problem_list(self, course_id, grader_id):
        return json.dumps({'success': True,
        'problem_list': [
          json.dumps({'location': 'i4x://MITx/3.091x/problem/open_ended_demo1',
            'problem_name': "Problem 1", 'num_graded': 3, 'num_pending': 5}),
          json.dumps({'location': 'i4x://MITx/3.091x/problem/open_ended_demo2',
            'problem_name': "Problem 2", 'num_graded': 1, 'num_pending': 5})
        ]})

class PeerGradingService(GradingService):
    """
    Interface with the grading controller for peer grading
    """
    def __init__(self, config):
        super(PeerGradingService, self).__init__(config)
        self.get_next_submission_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.is_student_calibrated_url = self.url + '/is_student_calibrated/'
        self.show_calibration_essay_url = self.url + '/show_calibration_essay/'
        self.save_calibration_essay_url = self.url + '/save_calibration_essay/'
        self.get_problem_list_url = self.url + '/get_problem_list/'

    def get_next_submission(self, problem_location, grader_id):
        response = self.get(self.get_next_submission_url, False, 
                {'location': problem_location, 'grader_id': grader_id})
        return response

    def save_grade(self, location, grader_id, submission_id, score, feedback, submission_key):
        data = {'grader_id' : grader_id,
                'submission_id' : submission_id,
                'score' : score,
                'feedback' : feedback,
                'submission_key': submission_key,
                'location': location}
        return self.post(self.save_grade_url, data)

    def is_student_calibrated(self, problem_location, grader_id):
        params = {'problem_id' : problem_location, 'student_id': grader_id}
        return self.get(self.is_student_calibrated_url, params)
    
    def show_calibration_essay(self, problem_location, grader_id):
        params = {'problem_id' : problem_location, 'student_id': grader_id}
        return self.get(self.show_calibration_essay_url, params)

    def save_calibration_essay(self, problem_location, grader_id, calibration_essay_id, submission_key, score, feedback):
        data = {'location': problem_location, 
                'student_id': grader_id, 
                'calibration_essay_id': calibration_essay_id,
                'submission_key': submission_key,
                'score': score,
                'feedback': feedback}
        return self.post(self.save_calibration_essay_url, data)

    def get_problem_list(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_problem_list_url, params)
        return response


_service = None
def peer_grading_service():
    """
    Return a peer grading service instance--if settings.MOCK_PEER_GRADING is True,
    returns a mock one, otherwise a real one.

    Caches the result, so changing the setting after the first call to this
    function will have no effect.
    """
    global _service
    if _service is not None:
        return _service

    if settings.MOCK_PEER_GRADING:
        _service = MockPeerGradingService()
    else:
        _service = PeerGradingService(settings.PEER_GRADING_INTERFACE)

    return _service

def _err_response(msg):
    """
    Return a HttpResponse with a json dump with success=False, and the given error message.
    """
    return HttpResponse(json.dumps({'success': False, 'error': msg}),
                        mimetype="application/json")

def _check_required(request, required):
    actual = set(request.POST.keys())
    missing = required - actual
    if len(missing) > 0:
        return False, "Missing required keys: {0}".format(', '.join(missing))
    else:
        return True, ""

def _check_post(request):
    if request.method != 'POST':
        raise Http404


def get_next_submission(request, course_id):
    """
    Makes a call to the grading controller for the next essay that should be graded
    Returns a json dict with the following keys:

    'success': bool

    'submission_id': a unique identifier for the submission, to be passed back
                     with the grade.

    'submission': the submission, rendered as read-only html for grading

    'rubric': the rubric, also rendered as html.

    'submission_key': a key associated with the submission for validation reasons

    'error': if success is False, will have an error message with more info.
    """
    _check_post(request)
    required = set(['location'])
    success, message = _check_required(request, required)
    if not success:
        return _err_response(message)
    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']

    try:
        response = peer_grading_service().get_next_submission(location, grader_id)
        return HttpResponse(response,
                        mimetype="application/json")
    except GradingServiceError:
        log.exception("Error getting next submission.  server url: {0}  location: {1}, grader_id: {2}"
                      .format(staff_grading_service().url, location, grader_id))
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})

def save_grade(request, course_id):
    """
    Saves the grade of a given submission.
    Input:
        The request should have the following keys:
        location - problem location
        submission_id - id associated with this submission
        submission_key - submission key given for validation purposes
        score - the grade that was given to the submission
        feedback - the feedback from the student
    Returns
        A json object with the following keys:
        success: bool indicating whether the save was a success
        error: if there was an error in the submission, this is the error message
    """
    _check_post(request)
    required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback'])
    success, message = _check_required(request, required)
    if not success:
        return _err_response(message)
    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']
    submission_id = p['submission_id']
    score = p['score']
    feedback = p['feedback']
    submission_key = p['submission_key']
    try:
        response = peer_grading_service().save_grade(location, grader_id, submission_id, 
                score, feedback, submission_key)
        return HttpResponse(response, mimetype="application/json")
    except GradingServiceError:
        log.exception("""Error saving grade.  server url: {0}, location: {1}, submission_id:{2}, 
                        submission_key: {3}, score: {4}"""
                      .format(staff_grading_service().url,
                          location, submission_id, submission_key, score)
                      )
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})



def is_student_calibrated(request, course_id):
    """
    Calls the grading controller to see if the given student is calibrated
    on the given problem

    Input:
        In the request, we need the following arguments:
        location - problem location

    Returns:
        Json object with the following keys
        success - bool indicating whether or not the call was successful
        calibrated - true if the grader has fully calibrated and can now move on to grading
                   - false if the grader is still working on calibration problems
        total_calibrated_on_so_far - the number of calibration essays for this problem 
            that this grader has graded
    """
    _check_post(request)
    required = set(['location'])
    success, message = _check_required(request, required)
    if not success:
        return _err_response(message)
    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']

    try:
        response = peer_grading_service().is_student_calibrated(location, grader_id)
        return HttpResponse(response, mimetype="application/json")
    except GradingServiceError:
        log.exception("Error from grading service.  server url: {0}, grader_id: {0}, location: {1}"
                      .format(staff_grading_service().url, grader_id, location))
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})



def show_calibration_essay(request, course_id):
    """
    Fetch the next calibration essay from the grading controller and return it
    Inputs:
        In the request
        location - problem location

    Returns:
        A json dict with the following keys
        'success': bool

        'submission_id': a unique identifier for the submission, to be passed back
                         with the grade.

        'submission': the submission, rendered as read-only html for grading

        'rubric': the rubric, also rendered as html.

        'submission_key': a key associated with the submission for validation reasons

        'error': if success is False, will have an error message with more info.

    """
    _check_post(request)

    required = set(['location'])
    success, message = _check_required(request, required)
    if not success:
        return _err_response(message)

    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']
    try:
        response = peer_grading_service().show_calibration_essay(location, grader_id)
        return HttpResponse(response, mimetype="application/json")
    except GradingServiceError:
        log.exception("Error from grading service.  server url: {0}, location: {0}"
                      .format(staff_grading_service().url, location))
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})


def save_calibration_essay(request, course_id):
    """
    Saves the grader's grade of a given calibration.
    Input:
        The request should have the following keys:
        location - problem location
        submission_id - id associated with this submission
        submission_key - submission key given for validation purposes
        score - the grade that was given to the submission
        feedback - the feedback from the student
    Returns
        A json object with the following keys:
        success: bool indicating whether the save was a success
        error: if there was an error in the submission, this is the error message
        actual_score: the score that the instructor gave to this calibration essay 

    """
    _check_post(request)

    required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback'])
    success, message = _check_required(request, required)
    if not success:
        return _err_response(message)
    grader_id = unique_id_for_user(request.user)
    p = request.POST
    location = p['location']
    calibration_essay_id = p['submission_id']
    submission_key = p['submission_key']
    score = p['score']
    feedback = p['feedback']

    try:
        response = peer_grading_service().save_calibration_essay(location, grader_id, calibration_essay_id, submission_key, score, feedback)
        return HttpResponse(response, mimetype="application/json")
    except GradingServiceError:
        log.exception("Error saving calibration grade, location: {0}, submission_id: {1}, submission_key: {2}, grader_id: {3}".format(location, submission_id, submission_key, grader_id))
        return _err_response('Could not connect to grading service')
