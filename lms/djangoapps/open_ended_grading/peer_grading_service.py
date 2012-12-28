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
                'submission_key', submission_key}
        return self.post(self.save_grade_url, False, data)
