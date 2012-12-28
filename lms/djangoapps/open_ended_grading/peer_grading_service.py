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

log = logging.getLogger(__name__)

class PeerGradingService(GradingService):
    """
    Interface with the grading controller for peer grading
    """
    def __init__(self, config):
        super(PeerGradingService, self).__init__(config)
        self.get_next_submission_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.is_student_calibrated_url = self.url + '/is_student_calibrated/'
        self.show_calibration_essay = self.url + '/show_calibration_essay/'
        self.save_calibration_essay = self.url + '/save_calibration_essay/'

    def get_next_submission(self, problem_location, grader_id):
        return self.get(self.get_next_submission_url, False, 
                {'location': problem_location, 'grader_id': grader_id})

    def save_grade(self, grader_id, submission_id, score, feedback, submission_key):
        data = {'grader_id' : grader_id,
                'submission_id' : submission_id,
                'score' : score,
                'feedback' : feedback,
                'submission_key': submission_key}
        return self.post(self.save_grade_url, False, data)


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

    _service = PeerGradingService(settings.PEER_GRADING_INTERFACE)

    return _service

def _err_response(msg):
    """
    Return a HttpResponse with a json dump with success=False, and the given error message.
    """
    return HttpResponse(json.dumps({'success': False, 'error': msg}),
                        mimetype="application/json")

def get_next_submission(request, course_id):
    required = set(['location'])
    if request.method != 'POST':
        raise Http404
    actual = set(request.POST.keys())
    missing = required - actual
    if len(missing) > 0:
        return _err_response('Missing required keys {0}'.format(
            ', '.join(missing)))
    grader_id = request.user.id
    p = request.POST
    location = p['location']

    return HttpResponse(_get_next(course_id, request.user.id, location),
                        mimetype="application/json")

def _get_next_submission(course_id, grader_id, location):
    """
    Implementation of get_next (also called from save_grade) -- returns a json string
    """
    try:
        return peer_grading_service().get_next_submission(location, grader_id)
    except GradingServiceError:
        log.exception("Error from grading service.  server url: {0}"
                      .format(staff_grading_service().url))
        return json.dumps({'success': False,
                           'error': 'Could not connect to grading service'})


