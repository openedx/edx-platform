import json
import logging

from lxml import etree

from datetime import datetime
from pkg_resources import resource_string
from .capa_module import ComplexEncoder
from .x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.modulestore.django import modulestore
from .timeinfo import TimeInfo
from xblock.core import Dict, String, Scope, Boolean, Integer, Float
from xmodule.fields import Date

from xmodule.open_ended_grading_classes.peer_grading_service import PeerGradingService, GradingServiceError, MockPeerGradingService
from open_ended_grading_classes import combined_open_ended_rubric
from django.utils.timezone import UTC

log = logging.getLogger(__name__)

USE_FOR_SINGLE_LOCATION = False
LINK_TO_LOCATION = ""
MAX_SCORE = 1
IS_GRADED = False

EXTERNAL_GRADER_NO_CONTACT_ERROR = "Failed to contact external graders.  Please notify course staff."


class PeerGradingFields(object):
    use_for_single_location = Boolean(
        display_name="Show Single Problem",
        help='When True, only the single problem specified by "Link to Problem Location" is shown. '
             'When False, a panel is displayed with all problems available for peer grading.',
        default=USE_FOR_SINGLE_LOCATION, scope=Scope.settings
    )
    link_to_location = String(
        display_name="Link to Problem Location",
        help='The location of the problem being graded. Only used when "Show Single Problem" is True.',
        default=LINK_TO_LOCATION, scope=Scope.settings
    )
    is_graded = Boolean(
        display_name="Graded",
        help='Defines whether the student gets credit for grading this problem. Only used when "Show Single Problem" is True.',
        default=IS_GRADED, scope=Scope.settings
    )
    due_date = Date(help="Due date that should be displayed.", default=None, scope=Scope.settings)
    grace_period_string = String(help="Amount of grace to give on the due date.", default=None, scope=Scope.settings)
    max_grade = Integer(
        help="The maximum grade that a student can receive for this problem.", default=MAX_SCORE,
        scope=Scope.settings, values={"min": 0}
    )
    student_data_for_location = Dict(
        help="Student data for a given peer grading problem.",
        scope=Scope.user_state
    )
    weight = Float(
        display_name="Problem Weight",
        help="Defines the number of points each problem is worth. If the value is not set, each problem is worth one point.",
        scope=Scope.settings, values={"min": 0, "step": ".1"}
    )


class PeerGradingModule(PeerGradingFields, XModule):
    """
    PeerGradingModule.__init__ takes the same arguments as xmodule.x_module:XModule.__init__
    """
    _VERSION = 1

    js = {'coffee': [resource_string(__name__, 'js/src/peergrading/peer_grading.coffee'),
                     resource_string(__name__, 'js/src/peergrading/peer_grading_problem.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
    ]}
    js_module_name = "PeerGrading"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, *args, **kwargs):
        super(PeerGradingModule, self).__init__(*args, **kwargs)

        #We need to set the location here so the child modules can use it
        self.runtime.set('location', self.location)
        if (self.system.open_ended_grading_interface):
            self.peer_gs = PeerGradingService(self.system.open_ended_grading_interface, self.system)
        else:
            self.peer_gs = MockPeerGradingService()

        if self.use_for_single_location:
            try:
                self.linked_problem = modulestore().get_instance(self.system.course_id, self.link_to_location)
            except:
                log.error("Linked location {0} for peer grading module {1} does not exist".format(
                    self.link_to_location, self.location))
                raise
            due_date = self.linked_problem._model_data.get('peer_grading_due', None)
            if due_date:
                self._model_data['due'] = due_date

        try:
            self.timeinfo = TimeInfo(self.due_date, self.grace_period_string)
        except:
            log.error("Error parsing due date information in location {0}".format(location))
            raise

        self.display_due_date = self.timeinfo.display_due_date

        try:
            self.student_data_for_location = json.loads(self.student_data_for_location)
        except:
            pass

        self.ajax_url = self.system.ajax_url
        if not self.ajax_url.endswith("/"):
            self.ajax_url = self.ajax_url + "/"

        # Integer could return None, so keep this check.
        if not isinstance(self.max_grade, int):
            raise TypeError("max_grade needs to be an integer.")

    def closed(self):
        return self._closed(self.timeinfo)

    def _closed(self, timeinfo):
        if timeinfo.close_date is not None and datetime.now(UTC()) > timeinfo.close_date:
            return True
        return False


    def _err_response(self, msg):
        """
        Return a HttpResponse with a json dump with success=False, and the given error message.
        """
        return {'success': False, 'error': msg}

    def _check_required(self, get, required):
        actual = set(get.keys())
        missing = required - actual
        if len(missing) > 0:
            return False, "Missing required keys: {0}".format(', '.join(missing))
        else:
            return True, ""

    def get_html(self):
        """
         Needs to be implemented by inheritors.  Renders the HTML that students see.
        @return:
        """
        if self.closed():
            return self.peer_grading_closed()
        if not self.use_for_single_location:
            return self.peer_grading()
        else:
            return self.peer_grading_problem({'location': self.link_to_location})['html']

    def handle_ajax(self, dispatch, get):
        """
        Needs to be implemented by child modules.  Handles AJAX events.
        @return:
        """
        handlers = {
            'get_next_submission': self.get_next_submission,
            'show_calibration_essay': self.show_calibration_essay,
            'is_student_calibrated': self.is_student_calibrated,
            'save_grade': self.save_grade,
            'save_calibration_essay': self.save_calibration_essay,
            'problem': self.peer_grading_problem,
        }

        if dispatch not in handlers:
            # This is a dev_facing_error
            log.error("Cannot find {0} in handlers in handle_ajax function for open_ended_module.py".format(dispatch))
            # This is a dev_facing_error
            return json.dumps({'error': 'Error handling action.  Please try again.', 'success': False})

        d = handlers[dispatch](get)

        return json.dumps(d, cls=ComplexEncoder)

    def query_data_for_location(self):
        student_id = self.system.anonymous_student_id
        location = self.link_to_location
        success = False
        response = {}

        try:
            response = self.peer_gs.get_data_for_location(location, student_id)
            count_graded = response['count_graded']
            count_required = response['count_required']
            success = True
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error getting location data from controller for location {0}, student {1}"
            .format(location, student_id))

        return success, response

    def get_progress(self):
        pass

    def get_score(self):
        max_score = None
        score = None
        score_dict = {
            'score': score,
            'total': max_score,
        }
        if not self.use_for_single_location or not self.is_graded:
            return score_dict

        try:
            count_graded = self.student_data_for_location['count_graded']
            count_required = self.student_data_for_location['count_required']
        except:
            success, response = self.query_data_for_location()
            if not success:
                log.exception(
                    "No instance data found and could not get data from controller for loc {0} student {1}".format(
                        self.system.location.url(), self.system.anonymous_student_id
                    ))
                return None
            count_graded = response['count_graded']
            count_required = response['count_required']
            if count_required > 0 and count_graded >= count_required:
                # Ensures that once a student receives a final score for peer grading, that it does not change.
                self.student_data_for_location = response

        if self.weight is not None:
            score = int(count_graded >= count_required and count_graded > 0) * float(self.weight)
            total = self.max_grade * float(self.weight)
            score_dict['score'] = score
            score_dict['total'] = total

        return score_dict

    def max_score(self):
        ''' Maximum score. Two notes:

            * This is generic; in abstract, a problem could be 3/5 points on one
              randomization, and 5/7 on another
        '''
        max_grade = None
        if self.use_for_single_location and self.is_graded:
            max_grade = self.max_grade
        return max_grade

    def get_next_submission(self, get):
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
        required = set(['location'])
        success, message = self._check_required(get, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id
        location = get['location']

        try:
            response = self.peer_gs.get_next_submission(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error getting next submission.  server url: {0}  location: {1}, grader_id: {2}"
            .format(self.peer_gs.url, location, grader_id))
            # This is a student_facing_error
            return {'success': False,
                    'error': EXTERNAL_GRADER_NO_CONTACT_ERROR}

    def save_grade(self, get):
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

        required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback', 'rubric_scores[]',
                        'submission_flagged'])
        success, message = self._check_required(get, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id

        location = get.get('location')
        submission_id = get.get('submission_id')
        score = get.get('score')
        feedback = get.get('feedback')
        submission_key = get.get('submission_key')
        rubric_scores = get.getlist('rubric_scores[]')
        submission_flagged = get.get('submission_flagged')

        try:
            response = self.peer_gs.save_grade(location, grader_id, submission_id,
                                               score, feedback, submission_key, rubric_scores, submission_flagged)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("""Error saving grade to open ended grading service.  server url: {0}, location: {1}, submission_id:{2},
                            submission_key: {3}, score: {4}"""
            .format(self.peer_gs.url,
                    location, submission_id, submission_key, score)
            )
            # This is a student_facing_error
            return {
                'success': False,
                'error': EXTERNAL_GRADER_NO_CONTACT_ERROR
            }

    def is_student_calibrated(self, get):
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

        required = set(['location'])
        success, message = self._check_required(get, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id

        location = get['location']

        try:
            response = self.peer_gs.is_student_calibrated(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error from open ended grading service.  server url: {0}, grader_id: {0}, location: {1}"
            .format(self.peer_gs.url, grader_id, location))
            # This is a student_facing_error
            return {
                'success': False,
                'error': EXTERNAL_GRADER_NO_CONTACT_ERROR
            }

    def show_calibration_essay(self, get):
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

        required = set(['location'])
        success, message = self._check_required(get, required)
        if not success:
            return self._err_response(message)

        grader_id = self.system.anonymous_student_id

        location = get['location']
        try:
            response = self.peer_gs.show_calibration_essay(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error from open ended grading service.  server url: {0}, location: {0}"
            .format(self.peer_gs.url, location))
            # This is a student_facing_error
            return {'success': False,
                    'error': EXTERNAL_GRADER_NO_CONTACT_ERROR}
        # if we can't parse the rubric into HTML,
        except etree.XMLSyntaxError:
            # This is a dev_facing_error
            log.exception("Cannot parse rubric string.")
            # This is a student_facing_error
            return {'success': False,
                    'error': 'Error displaying submission.  Please notify course staff.'}


    def save_calibration_essay(self, get):
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

        required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback', 'rubric_scores[]'])
        success, message = self._check_required(get, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id

        location = get.get('location')
        calibration_essay_id = get.get('submission_id')
        submission_key = get.get('submission_key')
        score = get.get('score')
        feedback = get.get('feedback')
        rubric_scores = get.getlist('rubric_scores[]')

        try:
            response = self.peer_gs.save_calibration_essay(location, grader_id, calibration_essay_id,
                                                           submission_key, score, feedback, rubric_scores)
            if 'actual_rubric' in response:
                rubric_renderer = combined_open_ended_rubric.CombinedOpenEndedRubric(self.system, True)
                response['actual_rubric'] = rubric_renderer.render_rubric(response['actual_rubric'])['html']
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception(
                "Error saving calibration grade, location: {0}, submission_key: {1}, grader_id: {2}".format(
                    location, submission_key, grader_id))
            # This is a student_facing_error
            return self._err_response('There was an error saving your score.  Please notify course staff.')

    def peer_grading_closed(self):
        '''
        Show the Peer grading closed template
        '''
        html = self.system.render_template('peer_grading/peer_grading_closed.html', {
            'use_for_single_location': self.use_for_single_location
        })
        return html


    def peer_grading(self, get=None):
        '''
        Show a peer grading interface
        '''

        # call problem list service
        success = False
        error_text = ""
        problem_list = []
        try:
            problem_list_json = self.peer_gs.get_problem_list(self.system.course_id, self.system.anonymous_student_id)
            problem_list_dict = problem_list_json
            success = problem_list_dict['success']
            if 'error' in problem_list_dict:
                error_text = problem_list_dict['error']

            problem_list = problem_list_dict['problem_list']

        except GradingServiceError:
            # This is a student_facing_error
            error_text = EXTERNAL_GRADER_NO_CONTACT_ERROR
            log.error(error_text)
            success = False
        # catch error if if the json loads fails
        except ValueError:
            # This is a student_facing_error
            error_text = "Could not get list of problems to peer grade.  Please notify course staff."
            log.error(error_text)
            success = False
        except:
            log.exception("Could not contact peer grading service.")
            success = False


        def _find_corresponding_module_for_location(location):
            '''
            find the peer grading module that links to the given location
            '''
            try:
                return modulestore().get_instance(self.system.course_id, location)
            except:
                # the linked problem doesn't exist
                log.error("Problem {0} does not exist in this course".format(location))
                raise

        for problem in problem_list:
            problem_location = problem['location']
            descriptor = _find_corresponding_module_for_location(problem_location)
            if descriptor:
                problem['due'] = descriptor._model_data.get('peer_grading_due', None)
                grace_period_string = descriptor._model_data.get('graceperiod', None)
                try:
                    problem_timeinfo = TimeInfo(problem['due'], grace_period_string)
                except:
                    log.error("Malformed due date or grace period string for location {0}".format(problem_location))
                    raise
                if self._closed(problem_timeinfo):
                    problem['closed'] = True
                else:
                    problem['closed'] = False
            else:
                # if we can't find the due date, assume that it doesn't have one
                problem['due'] = None
                problem['closed'] = False

        ajax_url = self.ajax_url
        html = self.system.render_template('peer_grading/peer_grading.html', {
            'course_id': self.system.course_id,
            'ajax_url': ajax_url,
            'success': success,
            'problem_list': problem_list,
            'error_text': error_text,
            # Checked above
            'staff_access': False,
            'use_single_location': self.use_for_single_location,
        })

        return html

    def peer_grading_problem(self, get=None):
        '''
        Show individual problem interface
        '''
        if get is None or get.get('location') is None:
            if not self.use_for_single_location:
                # This is an error case, because it must be set to use a single location to be called without get parameters
                # This is a dev_facing_error
                log.error(
                    "Peer grading problem in peer_grading_module called with no get parameters, but use_for_single_location is False.")
                return {'html': "", 'success': False}
            problem_location = self.link_to_location

        elif get.get('location') is not None:
            problem_location = get.get('location')

        ajax_url = self.ajax_url
        html = self.system.render_template('peer_grading/peer_grading_problem.html', {
            'view_html': '',
            'problem_location': problem_location,
            'course_id': self.system.course_id,
            'ajax_url': ajax_url,
            # Checked above
            'staff_access': False,
            'use_single_location': self.use_for_single_location,
        })

        return {'html': html, 'success': True}

    def get_instance_state(self):
        """
        Returns the current instance state.  The module can be recreated from the instance state.
        Input: None
        Output: A dictionary containing the instance state.
        """

        state = {
            'student_data_for_location': self.student_data_for_location,
        }

        return json.dumps(state)


class PeerGradingDescriptor(PeerGradingFields, RawDescriptor):
    """
    Module for adding peer grading questions
    """
    mako_template = "widgets/raw-edit.html"
    module_class = PeerGradingModule
    filename_extension = "xml"

    has_score = True
    always_recalculate_grades = True
    template_dir_name = "peer_grading"

    #Specify whether or not to pass in open ended interface
    needs_open_ended_interface = True

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(PeerGradingDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([PeerGradingFields.due_date, PeerGradingFields.grace_period_string,
                                    PeerGradingFields.max_grade])
        return non_editable_fields

