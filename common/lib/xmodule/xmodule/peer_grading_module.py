import json
import logging

from datetime import datetime

from django.utils.timezone import UTC
from lxml import etree
from pkg_resources import resource_string

from xblock.fields import Dict, String, Scope, Boolean, Float, Reference

from xmodule.capa_module import ComplexEncoder
from xmodule.fields import Date, Timedelta
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.raw_module import RawDescriptor
from xmodule.timeinfo import TimeInfo
from xmodule.x_module import XModule, module_attr
from xmodule.open_ended_grading_classes.peer_grading_service import PeerGradingService, MockPeerGradingService
from xmodule.open_ended_grading_classes.grading_service_module import GradingServiceError
from xmodule.validation import StudioValidation, StudioValidationMessage

from open_ended_grading_classes import combined_open_ended_rubric

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


EXTERNAL_GRADER_NO_CONTACT_ERROR = "Failed to contact external graders.  Please notify course staff."
MAX_ALLOWED_FEEDBACK_LENGTH = 5000


class PeerGradingFields(object):
    use_for_single_location = Boolean(
        display_name=_("Show Single Problem"),
        help=_('When True, only the single problem specified by "Link to Problem Location" is shown. '
               'When False, a panel is displayed with all problems available for peer grading.'),
        default=False,
        scope=Scope.settings
    )
    link_to_location = Reference(
        display_name=_("Link to Problem Location"),
        help=_('The location of the problem being graded. Only used when "Show Single Problem" is True.'),
        default="",
        scope=Scope.settings
    )
    graded = Boolean(
        display_name=_("Graded"),
        help=_('Defines whether the student gets credit for grading this problem. Only used when "Show Single Problem" is True.'),
        default=False,
        scope=Scope.settings
    )
    due = Date(
        help=_("Due date that should be displayed."),
        scope=Scope.settings)
    graceperiod = Timedelta(
        help=_("Amount of grace to give on the due date."),
        scope=Scope.settings
    )
    student_data_for_location = Dict(
        help=_("Student data for a given peer grading problem."),
        scope=Scope.user_state
    )
    weight = Float(
        display_name=_("Problem Weight"),
        help=_("Defines the number of points each problem is worth. If the value is not set, each problem is worth one point."),
        scope=Scope.settings, values={"min": 0, "step": ".1"},
        default=1
    )
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_("Peer Grading Interface")
    )
    data = String(
        help=_("Html contents to display for this module"),
        default='<peergrading></peergrading>',
        scope=Scope.content
    )


class InvalidLinkLocation(Exception):
    """
    Exception for the case in which a peer grading module tries to link to an invalid location.
    """
    pass


class PeerGradingModule(PeerGradingFields, XModule):
    """
    PeerGradingModule.__init__ takes the same arguments as xmodule.x_module:XModule.__init__
    """
    _VERSION = 1

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/peergrading/peer_grading.coffee'),
            resource_string(__name__, 'js/src/peergrading/peer_grading_problem.coffee'),
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }
    js_module_name = "PeerGrading"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, *args, **kwargs):
        super(PeerGradingModule, self).__init__(*args, **kwargs)

        # Copy this to a new variable so that we can edit it if needed.
        # We need to edit it if the linked module cannot be found, so
        # we can revert to panel model.
        self.use_for_single_location_local = self.use_for_single_location

        # We need to set the location here so the child modules can use it.
        self.runtime.set('location', self.location)
        if (self.runtime.open_ended_grading_interface):
            self.peer_gs = PeerGradingService(self.system.open_ended_grading_interface, self.system.render_template)
        else:
            self.peer_gs = MockPeerGradingService()

        if self.use_for_single_location_local:
            linked_descriptors = self.descriptor.get_required_module_descriptors()
            if len(linked_descriptors) == 0:
                error_msg = "Peer grading module {0} is trying to use single problem mode without "
                "a location specified.".format(self.location)
                log.error(error_msg)
                # Change module over to panel mode from single problem mode.
                self.use_for_single_location_local = False
            else:
                self.linked_problem = self.system.get_module(linked_descriptors[0])

        try:
            self.timeinfo = TimeInfo(self.due, self.graceperiod)
        except Exception:
            log.error("Error parsing due date information in location {0}".format(self.location))
            raise

        self.display_due_date = self.timeinfo.display_due_date

        try:
            self.student_data_for_location = json.loads(self.student_data_for_location)
        except Exception:  # pylint: disable=broad-except
            # OK with this broad exception because we just want to continue on any error
            pass

    @property
    def ajax_url(self):
        """
        Returns the `ajax_url` from the system, with any trailing '/' stripped off.
        """
        ajax_url = self.system.ajax_url
        if not ajax_url.endswith("/"):
            ajax_url += "/"
        return ajax_url

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

    def _check_required(self, data, required):
        actual = set(data.keys())
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
        if not self.use_for_single_location_local:
            return self.peer_grading()
        else:
            # b/c handle_ajax expects serialized data payload and directly calls peer_grading
            return self.peer_grading_problem({'location': self.link_to_location.to_deprecated_string()})['html']

    def handle_ajax(self, dispatch, data):
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

        data_dict = handlers[dispatch](data)

        return json.dumps(data_dict, cls=ComplexEncoder)

    def query_data_for_location(self, location):
        student_id = self.system.anonymous_student_id
        success = False
        response = {}

        try:
            response = self.peer_gs.get_data_for_location(location, student_id)
            _count_graded = response['count_graded']
            _count_required = response['count_required']
            success = True
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error getting location data from controller for location %s, student %s", location, student_id)

        return success, response

    def get_progress(self):
        pass

    def get_score(self):
        max_score = None
        score = None
        weight = self.weight

        #The old default was None, so set to 1 if it is the old default weight
        if weight is None:
            weight = 1
        score_dict = {
            'score': score,
            'total': max_score,
        }
        if not self.use_for_single_location_local or not self.graded:
            return score_dict

        try:
            count_graded = self.student_data_for_location['count_graded']
            count_required = self.student_data_for_location['count_required']
        except:
            success, response = self.query_data_for_location(self.link_to_location)
            if not success:
                log.exception(
                    "No instance data found and could not get data from controller for loc {0} student {1}".format(
                        self.system.location.to_deprecated_string(), self.system.anonymous_student_id
                    ))
                return None
            count_graded = response['count_graded']
            count_required = response['count_required']
            if count_required > 0 and count_graded >= count_required:
                # Ensures that once a student receives a final score for peer grading, that it does not change.
                self.student_data_for_location = response

        score = int(count_graded >= count_required and count_graded > 0) * float(weight)
        total = float(weight)
        score_dict['score'] = score
        score_dict['total'] = total

        return score_dict

    def max_score(self):
        ''' Maximum score. Two notes:

            * This is generic; in abstract, a problem could be 3/5 points on one
              randomization, and 5/7 on another
        '''
        max_grade = None
        if self.use_for_single_location_local and self.graded:
            max_grade = self.weight
        return max_grade

    def get_next_submission(self, data):
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
        success, message = self._check_required(data, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id
        location = data['location']

        try:
            response = self.peer_gs.get_next_submission(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error getting next submission.  server url: %s  location: %s, grader_id: %s", self.peer_gs.url, location, grader_id)
            # This is a student_facing_error
            return {'success': False,
                    'error': EXTERNAL_GRADER_NO_CONTACT_ERROR}

    def save_grade(self, data):
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

        required = ['location', 'submission_id', 'submission_key', 'score', 'feedback', 'submission_flagged', 'answer_unknown']
        if data.get("submission_flagged", False) in ["false", False, "False", "FALSE"]:
            required.append("rubric_scores[]")
        success, message = self._check_required(data, set(required))
        if not success:
            return self._err_response(message)

        success, message = self._check_feedback_length(data)
        if not success:
            return self._err_response(message)

        data_dict = {k: data.get(k) for k in required}
        if 'rubric_scores[]' in required:
            data_dict['rubric_scores'] = data.getall('rubric_scores[]')
        data_dict['grader_id'] = self.system.anonymous_student_id

        try:
            response = self.peer_gs.save_grade(**data_dict)
            success, location_data = self.query_data_for_location(data_dict['location'])
            #Don't check for success above because the response = statement will raise the same Exception as the one
            #that will cause success to be false.
            response.update({'required_done': False})
            if 'count_graded' in location_data and 'count_required' in location_data and int(location_data['count_graded']) >= int(location_data['count_required']):
                response['required_done'] = True
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error saving grade to open ended grading service.  server url: %s", self.peer_gs.url)

            # This is a student_facing_error
            return {
                'success': False,
                'error': EXTERNAL_GRADER_NO_CONTACT_ERROR
            }

    def is_student_calibrated(self, data):
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
        success, message = self._check_required(data, required)
        if not success:
            return self._err_response(message)
        grader_id = self.system.anonymous_student_id

        location = data['location']

        try:
            response = self.peer_gs.is_student_calibrated(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error from open ended grading service.  server url: %s, grader_id: %s, location: %s", self.peer_gs.url, grader_id, location)
            # This is a student_facing_error
            return {
                'success': False,
                'error': EXTERNAL_GRADER_NO_CONTACT_ERROR
            }

    def show_calibration_essay(self, data):
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
        success, message = self._check_required(data, required)
        if not success:
            return self._err_response(message)

        grader_id = self.system.anonymous_student_id

        location = data['location']
        try:
            response = self.peer_gs.show_calibration_essay(location, grader_id)
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error from open ended grading service.  server url: %s, location: %s", self.peer_gs.url, location)
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

    def save_calibration_essay(self, data):
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
        success, message = self._check_required(data, required)
        if not success:
            return self._err_response(message)

        data_dict = {k: data.get(k) for k in required}
        data_dict['rubric_scores'] = data.getall('rubric_scores[]')
        data_dict['student_id'] = self.system.anonymous_student_id
        data_dict['calibration_essay_id'] = data_dict['submission_id']

        try:
            response = self.peer_gs.save_calibration_essay(**data_dict)
            if 'actual_rubric' in response:
                rubric_renderer = combined_open_ended_rubric.CombinedOpenEndedRubric(self.system.render_template, True)
                response['actual_rubric'] = rubric_renderer.render_rubric(response['actual_rubric'])['html']
            return response
        except GradingServiceError:
            # This is a dev_facing_error
            log.exception("Error saving calibration grade")
            # This is a student_facing_error
            return self._err_response('There was an error saving your score.  Please notify course staff.')

    def peer_grading_closed(self):
        '''
        Show the Peer grading closed template
        '''
        html = self.system.render_template('peer_grading/peer_grading_closed.html', {
            'use_for_single_location': self.use_for_single_location_local
        })
        return html

    def _find_corresponding_module_for_location(self, location):
        """
        Find the peer grading module that exists at the given location.
        """
        try:
            return self.descriptor.system.load_item(location)
        except ItemNotFoundError:
            # The linked problem doesn't exist.
            log.error("Problem {0} does not exist in this course.".format(location))
            raise
        except NoPathToItem:
            # The linked problem does not have a path to it (ie is in a draft or other strange state).
            log.error("Cannot find a path to problem {0} in this course.".format(location))
            raise

    def peer_grading(self, _data=None):
        '''
        Show a peer grading interface
        '''

        # call problem list service
        success = False
        error_text = ""
        problem_list = []
        try:
            problem_list_dict = self.peer_gs.get_problem_list(self.course_id, self.system.anonymous_student_id)
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
        except Exception:
            log.exception("Could not contact peer grading service.")
            success = False

        good_problem_list = []
        for problem in problem_list:
            problem_location = problem['location']
            try:
                descriptor = self._find_corresponding_module_for_location(problem_location)
            except (NoPathToItem, ItemNotFoundError):
                continue
            if descriptor:
                problem['due'] = descriptor.due
                grace_period = descriptor.graceperiod
                try:
                    problem_timeinfo = TimeInfo(problem['due'], grace_period)
                except Exception:
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
            good_problem_list.append(problem)

        ajax_url = self.ajax_url
        html = self.system.render_template('peer_grading/peer_grading.html', {
            'ajax_url': ajax_url,
            'success': success,
            'problem_list': good_problem_list,
            'error_text': error_text,
            # Checked above
            'staff_access': False,
            'use_single_location': self.use_for_single_location_local,
        })

        return html

    def peer_grading_problem(self, data=None):
        '''
        Show individual problem interface
        '''
        if data is None or data.get('location') is None:
            if not self.use_for_single_location_local:
                # This is an error case, because it must be set to use a single location to be called without get parameters
                # This is a dev_facing_error
                log.error(
                    "Peer grading problem in peer_grading_module called with no get parameters, but use_for_single_location is False.")
                return {'html': "", 'success': False}
            problem_location = self.link_to_location

        elif data.get('location') is not None:
            problem_location = self.course_id.make_usage_key_from_deprecated_string(data.get('location'))

        self._find_corresponding_module_for_location(problem_location)

        ajax_url = self.ajax_url
        html = self.system.render_template('peer_grading/peer_grading_problem.html', {
            'view_html': '',
            'problem_location': problem_location,
            'course_id': self.course_id,
            'ajax_url': ajax_url,
            # Checked above
            'staff_access': False,
            'use_single_location': self.use_for_single_location_local,
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

    def _check_feedback_length(self, data):
        feedback = data.get("feedback")
        if feedback and len(feedback) > MAX_ALLOWED_FEEDBACK_LENGTH:
            return False, "Feedback is too long, Max length is {0} characters.".format(
                MAX_ALLOWED_FEEDBACK_LENGTH
            )
        else:
            return True, ""

    def validate(self):
        """
        Message for either error or warning validation message/s.

        Returns message and type. Priority given to error type message.
        """
        return self.descriptor.validate()


class PeerGradingDescriptor(PeerGradingFields, RawDescriptor):
    """
    Module for adding peer grading questions
    """
    mako_template = "widgets/raw-edit.html"
    module_class = PeerGradingModule
    filename_extension = "xml"

    has_score = True
    always_recalculate_grades = True

    #Specify whether or not to pass in open ended interface
    needs_open_ended_interface = True

    metadata_translations = {
        'is_graded': 'graded',
        'attempts': 'max_attempts',
        'due_data': 'due'
    }

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(PeerGradingDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([PeerGradingFields.due, PeerGradingFields.graceperiod])
        return non_editable_fields

    def get_required_module_descriptors(self):
        """
        Returns a list of XModuleDescriptor instances upon which this module depends, but are
        not children of this module.
        """

        # If use_for_single_location is True, this is linked to an open ended problem.
        if self.use_for_single_location:
            # Try to load the linked module.
            # If we can't load it, return empty list to avoid exceptions on progress page.
            try:
                linked_module = self.system.load_item(self.link_to_location)
                return [linked_module]
            except (NoPathToItem, ItemNotFoundError):
                error_message = ("Cannot find the combined open ended module "
                                 "at location {0} being linked to from peer "
                                 "grading module {1}").format(self.link_to_location, self.location)
                log.error(error_message)
                return []
        else:
            return []

    # Proxy to PeerGradingModule so that external callers don't have to know if they're working
    # with a module or a descriptor
    closed = module_attr('closed')
    get_instance_state = module_attr('get_instance_state')
    get_next_submission = module_attr('get_next_submission')
    graded = module_attr('graded')
    is_student_calibrated = module_attr('is_student_calibrated')
    peer_grading = module_attr('peer_grading')
    peer_grading_closed = module_attr('peer_grading_closed')
    peer_grading_problem = module_attr('peer_grading_problem')
    peer_gs = module_attr('peer_gs')
    query_data_for_location = module_attr('query_data_for_location')
    save_calibration_essay = module_attr('save_calibration_essay')
    save_grade = module_attr('save_grade')
    show_calibration_essay = module_attr('show_calibration_essay')
    use_for_single_location_local = module_attr('use_for_single_location_local')
    _find_corresponding_module_for_location = module_attr('_find_corresponding_module_for_location')

    def validate(self):
        """
        Validates the state of this instance. This is the override of the general XBlock method,
        and it will also ask its superclass to validate.
        """
        validation = super(PeerGradingDescriptor, self).validate()
        validation = StudioValidation.copy(validation)

        i18n_service = self.runtime.service(self, "i18n")

        validation.summary = StudioValidationMessage(
            StudioValidationMessage.ERROR,
            i18n_service.ugettext(
                "ORA1 is no longer supported. To use this assessment, "
                "replace this ORA1 component with an ORA2 component."
            )
        )
        return validation
