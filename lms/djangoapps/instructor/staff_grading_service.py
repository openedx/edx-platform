"""
This module provides views that proxy to the staff grading backend service.
"""

import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

from django.conf import settings
from django.http import HttpResponse, Http404

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor

log = logging.getLogger(__name__)


class GradingServiceError(Exception):
    pass


class MockStaffGradingService(object):
    """
    A simple mockup of a staff grading service, testing.
    """
    def __init__(self):
        self.cnt = 0

    def get_next(self, course_id, grader_id):
        self.cnt += 1
        return json.dumps({'success': True,
                           'submission_id': self.cnt,
                           'submission': 'Test submission {cnt}'.format(cnt=self.cnt),
                           'max_score': 2 + self.cnt % 3,
                           'rubric': 'A rubric'})

    def save_grade(self, course_id, grader_id, submission_id, score, feedback):
        return self.get_next(course_id, grader_id)


class StaffGradingService(object):
    """
    Interface to staff grading backend.
    """
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.url = config['url']

        self.login_url = self.url + '/login/'
        self.get_next_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'

        self.session = requests.session()


    def _login(self):
        """
        Log into the staff grading service.

        Raises requests.exceptions.HTTPError if something goes wrong.

        Returns the decoded json dict of the response.
        """
        response = self.session.post(self.login_url,
                                     {'username': self.username,
                                      'password': self.password,})

        response.raise_for_status()

        return response.json


    def _try_with_login(self, operation):
        """
        Call operation(), which should return a requests response object.  If
        the response status code is 302, call _login() and try the operation
        again.  NOTE: use requests.get(..., allow_redirects=False) to have
        requests not auto-follow redirects.

        Returns the result of operation().  Does not catch exceptions.
        """
        response = operation()
        if response.status_code == 302:
            # redirect means we aren't logged in
            r = self._login()
            if r and not r.get('success'):
                log.warning("Couldn't log into staff_grading backend. Response: %s",
                            r)
            # try again
            return operation()

        return response


    def get_next(self, course_id, grader_id):
        """
        Get the next thing to grade.  Returns json, or raises GradingServiceError
        if there's a problem.
        """
        op = lambda: self.session.get(self.get_next_url,
                                      allow_redirects=False,
                                      params={'course_id': course_id,
                                              'grader_id': grader_id})
        try:
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text

    
    def save_grade(self, course_id, grader_id, submission_id, score, feedback):
        """
        Save a score and feedback for a submission.

        Returns json dict with keys
           'success': bool
           'error': error msg, if something went wrong.

        Raises GradingServiceError if there's a problem connecting.
        """
        try:
            data = {'course_id': course_id,
                    'submission_id': submission_id,
                    'score': score,
                    'feedback': feedback,
                    'grader_id': grader_id}

            op = lambda: self.session.post(self.save_grade_url, data=data,
                                           allow_redirects=False)
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text

# don't initialize until grading_service() is called--means that just
# importing this file doesn't create objects that may not have the right config
_service = None

def grading_service():
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
    Get the next thing to grade for course_id.

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

    return HttpResponse(_get_next(course_id, request.user.id),
                        mimetype="application/json")


def _get_next(course_id, grader_id):
    """
    Implementation of get_next (also called from save_grade) -- returns a json string
    """

    try:
        return grading_service().get_next(course_id, grader_id)
    except GradingServiceError:
        log.exception("Error from grading service")
        return json.dumps({'success': False, 'error': 'Could not connect to grading service'})


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

    required = ('score', 'feedback', 'submission_id')
    for k in required:
        if k not in request.POST.keys():
            return _err_response('Missing required key {0}'.format(k))

    grader_id = request.user.id
    p = request.POST

    try:
        result_json = grading_service().save_grade(course_id,
                                          grader_id,
                                          p['submission_id'],
                                          p['score'],
                                          p['feedback'])
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
    return HttpResponse(_get_next(course_id, grader_id),
                        mimetype="application/json")

