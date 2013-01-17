import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys
from grading_service import GradingService
from grading_service import GradingServiceError

from django.conf import settings
from django.http import HttpResponse, Http404

log = logging.getLogger(__name__)

class ControllerQueryService(GradingService):
    """
    Interface to staff grading backend.
    """
    def __init__(self, config):
        super(ControllerQuery, self).__init__(config)
        self.check_eta_url = self.url + '/get_submission_eta/'
        self.is_unique_url = self.url + '/is_name_unique/'

    def check_if_name_is_unique(self, location, problem_id, course_id):
        params = {
            'course_id': course_id,
            'location' : location,
            'problem_id' : problem_id
        }
        response = self.get(self.is_unique_url, params)
        return response

    def check_for_eta(self, location):
        params = {
            'location' : location,
        }
        response = self.get(self.check_eta_url, params)
        return response
