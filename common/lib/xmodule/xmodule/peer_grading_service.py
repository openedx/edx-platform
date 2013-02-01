import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

from django.conf import settings
from django.http import HttpResponse, Http404

from combined_open_ended_rubric import CombinedOpenEndedRubric, RubricParsingError
from lxml import etree

log=logging.getLogger(__name__)

class GradingServiceError(Exception):
    pass

class PeerGradingService():
    """
    Interface with the grading controller for peer grading
    """
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.url = config['url']
        self.login_url = self.url + '/login/'
        self.session = requests.session()
        self.get_next_submission_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.is_student_calibrated_url = self.url + '/is_student_calibrated/'
        self.show_calibration_essay_url = self.url + '/show_calibration_essay/'
        self.save_calibration_essay_url = self.url + '/save_calibration_essay/'
        self.get_problem_list_url = self.url + '/get_problem_list/'
        self.get_notifications_url = self.url + '/get_notifications/'

    def get_next_submission(self, problem_location, grader_id):
        response = self.get(self.get_next_submission_url,
            {'location': problem_location, 'grader_id': grader_id})
        return json.dumps(self._render_rubric(response))

    def save_grade(self, location, grader_id, submission_id, score, feedback, submission_key, rubric_scores, submission_flagged):
        data = {'grader_id' : grader_id,
                'submission_id' : submission_id,
                'score' : score,
                'feedback' : feedback,
                'submission_key': submission_key,
                'location': location,
                'rubric_scores': rubric_scores,
                'rubric_scores_complete': True,
                'submission_flagged' : submission_flagged}
        log.debug(data)
        return self.post(self.save_grade_url, data)

    def is_student_calibrated(self, problem_location, grader_id):
        params = {'problem_id' : problem_location, 'student_id': grader_id}
        return self.get(self.is_student_calibrated_url, params)

    def show_calibration_essay(self, problem_location, grader_id):
        params = {'problem_id' : problem_location, 'student_id': grader_id}
        response = self.get(self.show_calibration_essay_url, params)
        return json.dumps(self._render_rubric(response))

    def save_calibration_essay(self, problem_location, grader_id, calibration_essay_id, submission_key,
                               score, feedback, rubric_scores):
        data = {'location': problem_location,
                'student_id': grader_id,
                'calibration_essay_id': calibration_essay_id,
                'submission_key': submission_key,
                'score': score,
                'feedback': feedback,
                'rubric_scores[]': rubric_scores,
                'rubric_scores_complete': True}
        log.debug(data)
        return self.post(self.save_calibration_essay_url, data)

    def get_problem_list(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_problem_list_url, params)
        return response

    def get_notifications(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_notifications_url, params)
        return response

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

    def post(self, url, data, allow_redirects=False):
        """
        Make a post request to the grading controller
        """
        try:
            op = lambda: self.session.post(url, data=data,
                allow_redirects=allow_redirects)
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text

    def get(self, url, params, allow_redirects=False):
        """
        Make a get request to the grading controller
        """
        log.debug(params)
        op = lambda: self.session.get(url,
            allow_redirects=allow_redirects,
            params=params)
        try:
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text


    def _try_with_login(self, operation):
        """
        Call operation(), which should return a requests response object.  If
        the request fails with a 'login_required' error, call _login() and try
        the operation again.

        Returns the result of operation().  Does not catch exceptions.
        """
        response = operation()
        if (response.json
            and response.json.get('success') == False
            and response.json.get('error') == 'login_required'):
            # apparrently we aren't logged in.  Try to fix that.
            r = self._login()
            if r and not r.get('success'):
                log.warning("Couldn't log into peer grading backend. Response: %s",
                    r)
                # try again
            response = operation()
            response.raise_for_status()

        return response

    def _render_rubric(self, response, view_only=False):
        """
        Given an HTTP Response with the key 'rubric', render out the html
        required to display the rubric and put it back into the response

        returns the updated response as a dictionary that can be serialized later

        """
        try:
            response_json = json.loads(response)
            if 'rubric' in response_json:
                rubric = response_json['rubric']
                rubric_renderer = CombinedOpenEndedRubric(self.system, False)
                success, rubric_html = rubric_renderer.render_rubric(rubric)
                response_json['rubric'] = rubric_html
            return response_json
        # if we can't parse the rubric into HTML, 
        except etree.XMLSyntaxError, RubricParsingError:
            log.exception("Cannot parse rubric string. Raw string: {0}"
            .format(rubric))
            return {'success': False,
                    'error': 'Error displaying submission'}
        except ValueError:
            log.exception("Error parsing response: {0}".format(response))
            return {'success': False,
                    'error': "Error displaying submission"}

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
