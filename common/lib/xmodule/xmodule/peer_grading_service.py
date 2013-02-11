import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

#TODO: Settings import is needed now in order to specify the URL where to find the peer grading service.
#Eventually, the goal is to replace the global django settings import with settings specifically
#for this xmodule.  There is no easy way to do this now, so piggybacking on the django settings
#makes sense.
from django.conf import settings

from combined_open_ended_rubric import CombinedOpenEndedRubric, RubricParsingError
from lxml import etree
from grading_service_module import GradingService, GradingServiceError

log = logging.getLogger(__name__)


class GradingServiceError(Exception):
    pass


class PeerGradingService(GradingService):
    """
    Interface with the grading controller for peer grading
    """
    def __init__(self, config, system):
        config['system'] = system
        super(PeerGradingService, self).__init__(config)
        self.url = config['url'] + config['peer_grading']
        self.get_next_submission_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.is_student_calibrated_url = self.url + '/is_student_calibrated/'
        self.show_calibration_essay_url = self.url + '/show_calibration_essay/'
        self.save_calibration_essay_url = self.url + '/save_calibration_essay/'
        self.get_problem_list_url = self.url + '/get_problem_list/'
        self.get_notifications_url = self.url + '/get_notifications/'
        self.get_data_for_location_url = self.url + '/get_data_for_location/'
        self.system = system

    def get_data_for_location(self, problem_location, student_id):
        response = self.get(self.get_data_for_location_url,
            {'location': problem_location, 'student_id': student_id})
        return self.try_to_decode(response)

    def get_next_submission(self, problem_location, grader_id):
        response = self.get(self.get_next_submission_url,
            {'location': problem_location, 'grader_id': grader_id})
        return self.try_to_decode(self._render_rubric(response))

    def save_grade(self, location, grader_id, submission_id, score, feedback, submission_key, rubric_scores, submission_flagged):
        data = {'grader_id': grader_id,
                'submission_id': submission_id,
                'score': score,
                'feedback': feedback,
                'submission_key': submission_key,
                'location': location,
                'rubric_scores': rubric_scores,
                'rubric_scores_complete': True,
                'submission_flagged': submission_flagged}
        return self.try_to_decode(self.post(self.save_grade_url, data))

    def is_student_calibrated(self, problem_location, grader_id):
        params = {'problem_id': problem_location, 'student_id': grader_id}
        return self.try_to_decode(self.get(self.is_student_calibrated_url, params))

    def show_calibration_essay(self, problem_location, grader_id):
        params = {'problem_id': problem_location, 'student_id': grader_id}
        response = self.get(self.show_calibration_essay_url, params)
        return self.try_to_decode(self._render_rubric(response))

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
        return self.try_to_decode(self.post(self.save_calibration_essay_url, data))

    def get_problem_list(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_problem_list_url, params)
        return self.try_to_decode(response)

    def get_notifications(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_notifications_url, params)
        return self.try_to_decode(response)

    def try_to_decode(self, text):
        try:
            text = json.loads(text)
        except:
            pass
        return text

"""
This is a mock peer grading service that can be used for unit tests
without making actual service calls to the grading controller
"""


class MockPeerGradingService(object):
    def get_next_submission(self, problem_location, grader_id):
        return json.dumps({'success': True,
                           'submission_id': 1,
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
                           'submission_id': 1,
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


def peer_grading_service(system):
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
        _service = PeerGradingService(settings.OPEN_ENDED_GRADING_INTERFACE, system)

    return _service
