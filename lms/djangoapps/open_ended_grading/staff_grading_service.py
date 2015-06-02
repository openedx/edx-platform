"""
This module provides views that proxy to the staff grading backend service.
"""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.open_ended_grading_classes.grading_service_module import GradingService, GradingServiceError

from courseware.access import has_access
from edxmako.shortcuts import render_to_string
from student.models import unique_id_for_user

from open_ended_grading.utils import does_location_exist
import dogstats_wrapper as dog_stats_api

log = logging.getLogger(__name__)

STAFF_ERROR_MESSAGE = _(
    u'Could not contact the external grading server. Please contact the '
    u'development team at {email}.'
).format(
    email=u'<a href="mailto:{tech_support_email}>{tech_support_email}</a>'.format(
        tech_support_email=settings.TECH_SUPPORT_EMAIL
    )
)
MAX_ALLOWED_FEEDBACK_LENGTH = 5000


class MockStaffGradingService(object):
    """
    A simple mockup of a staff grading service, testing.
    """

    def __init__(self):
        self.cnt = 0

    def get_next(self, course_id, location, grader_id):
        self.cnt += 1
        return {'success': True,
                'submission_id': self.cnt,
                'submission': 'Test submission {cnt}'.format(cnt=self.cnt),
                'num_graded': 3,
                'min_for_ml': 5,
                'num_pending': 4,
                'prompt': 'This is a fake prompt',
                'ml_error_info': 'ML info',
                'max_score': 2 + self.cnt % 3,
                'rubric': 'A rubric'}

    def get_problem_list(self, course_id, grader_id):
        self.cnt += 1
        return {
            'success': True,
            'problem_list': [
                json.dumps({
                    'location': 'i4x://MITx/3.091x/problem/open_ended_demo1',
                    'problem_name': "Problem 1",
                    'num_graded': 3,
                    'num_pending': 5,
                    'min_for_ml': 10,
                }),
                json.dumps({
                    'location': 'i4x://MITx/3.091x/problem/open_ended_demo2',
                    'problem_name': "Problem 2",
                    'num_graded': 1,
                    'num_pending': 5,
                    'min_for_ml': 10,
                }),
            ],
        }

    def save_grade(self, course_id, grader_id, submission_id, score, feedback, skipped, rubric_scores,
                   submission_flagged):
        return self.get_next(course_id, 'fake location', grader_id)


class StaffGradingService(GradingService):
    """
    Interface to staff grading backend.
    """

    METRIC_NAME = 'edxapp.open_ended_grading.staff_grading_service'

    def __init__(self, config):
        config['render_template'] = render_to_string
        super(StaffGradingService, self).__init__(config)
        self.url = config['url'] + config['staff_grading']
        self.login_url = self.url + '/login/'
        self.get_next_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.get_problem_list_url = self.url + '/get_problem_list/'
        self.get_notifications_url = self.url + "/get_notifications/"

    def get_problem_list(self, course_id, grader_id):
        """
        Get the list of problems for a given course.

        Args:
            course_id: course id that we want the problems of
            grader_id: who is grading this?  The anonymous user_id of the grader.

        Returns:
            dict with the response from the service.  (Deliberately not
            writing out the fields here--see the docs on the staff_grading view
            in the grading_controller repo)

        Raises:
            GradingServiceError: something went wrong with the connection.
        """
        params = {'course_id': course_id.to_deprecated_string(), 'grader_id': grader_id}
        result = self.get(self.get_problem_list_url, params)
        tags = [u'course_id:{}'.format(course_id)]
        self._record_result('get_problem_list', result, tags)
        dog_stats_api.histogram(
            self._metric_name('get_problem_list.result.length'),
            len(result.get('problem_list', []))
        )
        return result

    def get_next(self, course_id, location, grader_id):
        """
        Get the next thing to grade.

        Args:
            course_id: the course that this problem belongs to
            location: location of the problem that we are grading and would like the
                next submission for
            grader_id: who is grading this?  The anonymous user_id of the grader.

        Returns:
            dict with the response from the service.  (Deliberately not
            writing out the fields here--see the docs on the staff_grading view
            in the grading_controller repo)

        Raises:
            GradingServiceError: something went wrong with the connection.
        """
        result = self._render_rubric(
            self.get(
                self.get_next_url,
                params={
                    'location': location.to_deprecated_string(),
                    'grader_id': grader_id
                }
            )
        )
        tags = [u'course_id:{}'.format(course_id)]
        self._record_result('get_next', result, tags)
        return result

    def save_grade(self, course_id, grader_id, submission_id, score, feedback, skipped, rubric_scores,
                   submission_flagged):
        """
        Save a score and feedback for a submission.

        Returns:
            dict with keys
                'success': bool
                'error': error msg, if something went wrong.

        Raises:
            GradingServiceError if there's a problem connecting.
        """
        data = {'course_id': course_id.to_deprecated_string(),
                'submission_id': submission_id,
                'score': score,
                'feedback': feedback,
                'grader_id': grader_id,
                'skipped': skipped,
                'rubric_scores': rubric_scores,
                'rubric_scores_complete': True,
                'submission_flagged': submission_flagged}

        result = self._render_rubric(self.post(self.save_grade_url, data=data))
        tags = [u'course_id:{}'.format(course_id)]
        self._record_result('save_grade', result, tags)
        return result

    def get_notifications(self, course_id):
        params = {'course_id': course_id.to_deprecated_string()}
        result = self.get(self.get_notifications_url, params)
        tags = [
            u'course_id:{}'.format(course_id),
            u'staff_needs_to_grade:{}'.format(result.get('staff_needs_to_grade'))
        ]
        self._record_result('get_notifications', result, tags)
        return result


# don't initialize until staff_grading_service() is called--means that just
# importing this file doesn't create objects that may not have the right config
_service = None


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
        _service = StaffGradingService(settings.OPEN_ENDED_GRADING_INTERFACE)

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
    if not has_access(user, 'staff', course_id):
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
    assert(isinstance(course_id, basestring))
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    _check_access(request.user, course_key)

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
    location = course_key.make_usage_key_from_deprecated_string(p['location'])

    return HttpResponse(json.dumps(_get_next(course_key, grader_id, location)),
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

        'error': if success is False, will have an error message with more info.
    """
    assert(isinstance(course_id, basestring))
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    _check_access(request.user, course_key)
    try:
        response = staff_grading_service().get_problem_list(course_key, unique_id_for_user(request.user))

        # If 'problem_list' is in the response, then we got a list of problems from the ORA server.
        # If it is not, then ORA could not find any problems.
        if 'problem_list' in response:
            problem_list = response['problem_list']
        else:
            problem_list = []
            # Make an error messages to reflect that we could not find anything to grade.
            response['error'] = _(
                u'Cannot find any open response problems in this course. '
                u'Have you submitted answers to any open response assessment questions? '
                u'If not, please do so and return to this page.'
            )
        valid_problem_list = []
        for i in xrange(len(problem_list)):
            # Needed to ensure that the 'location' key can be accessed.
            try:
                problem_list[i] = json.loads(problem_list[i])
            except Exception:
                pass
            if does_location_exist(course_key.make_usage_key_from_deprecated_string(problem_list[i]['location'])):
                valid_problem_list.append(problem_list[i])
        response['problem_list'] = valid_problem_list
        response = json.dumps(response)

        return HttpResponse(response,
                            mimetype="application/json")
    except GradingServiceError:
        #This is a dev_facing_error
        log.exception(
            "Error from staff grading service in open "
            "ended grading.  server url: {0}".format(staff_grading_service().url)
        )
        #This is a staff_facing_error
        return HttpResponse(json.dumps({'success': False,
                                        'error': STAFF_ERROR_MESSAGE}))


def _get_next(course_id, grader_id, location):
    """
    Implementation of get_next (also called from save_grade) -- returns a json string
    """
    try:
        return staff_grading_service().get_next(course_id, location, grader_id)
    except GradingServiceError:
        #This is a dev facing error
        log.exception(
            "Error from staff grading service in open "
            "ended grading.  server url: {0}".format(staff_grading_service().url)
        )
        #This is a staff_facing_error
        return json.dumps({'success': False,
                           'error': STAFF_ERROR_MESSAGE})


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

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    _check_access(request.user, course_key)

    if request.method != 'POST':
        raise Http404
    p = request.POST
    required = set(['score', 'feedback', 'submission_id', 'location', 'submission_flagged'])
    skipped = 'skipped' in p
    #If the instructor has skipped grading the submission, then there will not be any rubric scores.
    #Only add in the rubric scores if the instructor has not skipped.
    if not skipped:
        required.add('rubric_scores[]')
    actual = set(p.keys())
    missing = required - actual
    if len(missing) > 0:
        return _err_response('Missing required keys {0}'.format(
            ', '.join(missing)))

    success, message = check_feedback_length(p)
    if not success:
        return _err_response(message)

    grader_id = unique_id_for_user(request.user)

    location = course_key.make_usage_key_from_deprecated_string(p['location'])

    try:
        result = staff_grading_service().save_grade(course_key,
                                                    grader_id,
                                                    p['submission_id'],
                                                    p['score'],
                                                    p['feedback'],
                                                    skipped,
                                                    p.getlist('rubric_scores[]'),
                                                    p['submission_flagged'])
    except GradingServiceError:
        #This is a dev_facing_error
        log.exception(
            "Error saving grade in the staff grading interface in open ended grading.  Request: {0} Course ID: {1}".format(
                request, course_id))
        #This is a staff_facing_error
        return _err_response(STAFF_ERROR_MESSAGE)
    except ValueError:
        #This is a dev_facing_error
        log.exception(
            "save_grade returned broken json in the staff grading interface in open ended grading: {0}".format(
                result_json))
        #This is a staff_facing_error
        return _err_response(STAFF_ERROR_MESSAGE)

    if not result.get('success', False):
        #This is a dev_facing_error
        log.warning(
            'Got success=False from staff grading service in open ended grading.  Response: {0}'.format(result_json))
        return _err_response(STAFF_ERROR_MESSAGE)

    # Ok, save_grade seemed to work.  Get the next submission to grade.
    return HttpResponse(json.dumps(_get_next(course_id, grader_id, location)),
                        mimetype="application/json")


def check_feedback_length(data):
    feedback = data.get("feedback")
    if feedback and len(feedback) > MAX_ALLOWED_FEEDBACK_LENGTH:
        return False, "Feedback is too long, Max length is {0} characters.".format(
            MAX_ALLOWED_FEEDBACK_LENGTH
        )
    else:
        return True, ""
