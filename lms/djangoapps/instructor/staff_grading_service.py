"""
This module provides views that proxy to the staff grading backend service.
"""

import json
import requests
import sys

from django.http import Http404
from django.http import HttpResponse


from util.json_request import expect_json

class GradingServiceError(Exception):
    pass

class StaffGradingService(object):
    """
    Interface to staff grading backend.
    """
    def __init__(self, url):
        self.url = url
        # TODO: add auth
        self.session = requests.session()

    def get_next(course_id):
        """
        Get the next thing to grade.  Returns json, or raises GradingServiceError
        if there's a problem.
        """
        try:
            r = self.session.get(url + 'get_next')
        except requests.exceptions.ConnectionError as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text


#@login_required
def get_next(request, course_id):
    """
    """
    d = {'success': False}
    return HttpResponse(json.dumps(d))


#@login_required
@expect_json
def save_grade(request, course_id):
    """

    """
    d = {'success': False}
    return HttpResponse(json.dumps(d))

