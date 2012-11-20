"""
This module provides views that proxy to the staff grading backend service.
"""

import json
import logging
import requests
import sys

from django.conf import settings
from django.http import HttpResponse, Http404

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor

log = logging.getLogger("mitx.courseware")


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
        return self.get_next(course_id)


class StaffGradingService(object):
    """
    Interface to staff grading backend.
    """
    def __init__(self, url):
        self.url = url
        self.get_next_url = url + '/get_next_submission/'
        self.save_grade_url = url + '/save_grade/'
        # TODO: add auth
        self.session = requests.session()

    def get_next(self, course_id, grader_id):
        """
        Get the next thing to grade.  Returns json, or raises GradingServiceError
        if there's a problem.
        """
        try:
            r = self.session.get(self.get_next_url,
                                 params={'course_id': course_id,
                                         'grader_id': grader_id})
        except requests.exceptions.ConnectionError as err:
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
            
            r = self.session.post(self.save_grade_url, data=data)
        except requests.exceptions.ConnectionError as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text

_service = StaffGradingService(settings.STAFF_GRADING_BACKEND_URL)
#_service = MockStaffGradingService()

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
        return _service.get_next(course_id, grader_id)
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
        result_json = _service.save_grade(course_id,
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

