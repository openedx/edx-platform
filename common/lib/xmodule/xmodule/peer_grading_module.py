"""
This module provides an interface on the grading-service backend
for peer grading

Use peer_grading_service() to get the version specified
in settings.PEER_GRADING_INTERFACE

"""
import json
import logging
import requests
import sys

from django.conf import settings

from combined_open_ended_rubric import CombinedOpenEndedRubric
from lxml import etree

import copy
import itertools
import json
import logging
from lxml.html import rewrite_links
import os

from pkg_resources import resource_string
from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from progress import Progress
from .stringify import stringify_children
from .x_module import XModule
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location

from peer_grading_service import peer_grading_service, GradingServiceError

log = logging.getLogger(__name__)

USE_FOR_SINGLE_LOCATION = False
LINK_TO_LOCATION = ""
TRUE_DICT = [True, "True", "true", "TRUE"]
MAX_SCORE = 1
IS_GRADED = True

class PeerGradingModule(XModule):
    _VERSION = 1

    js = {'coffee': [resource_string(__name__, 'js/src/peergrading/peer_grading.coffee'),
                     resource_string(__name__, 'js/src/peergrading/peer_grading_problem.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     ]}
    js_module_name = "PeerGrading"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        # Load instance state
        if instance_state is not None:
            instance_state = json.loads(instance_state)
        else:
            instance_state = {}

        #We need to set the location here so the child modules can use it
        system.set('location', location)
        self.system = system
        self.peer_gs = peer_grading_service(self.system)

        self.use_for_single_location = self.metadata.get('use_for_single_location', USE_FOR_SINGLE_LOCATION)
        if isinstance(self.use_for_single_location, basestring):
            self.use_for_single_location = (self.use_for_single_location in TRUE_DICT)

        self.is_graded = self.metadata.get('is_graded', IS_GRADED)
        if isinstance(self.is_graded, basestring):
            self.is_graded = (self.is_graded in TRUE_DICT)

        self.link_to_location = self.metadata.get('link_to_location', USE_FOR_SINGLE_LOCATION)
        if self.use_for_single_location ==True:
            #This will raise an exception if the location is invalid
            link_to_location_object = Location(self.link_to_location)

        self.ajax_url = self.system.ajax_url
        if not self.ajax_url.endswith("/"):
            self.ajax_url = self.ajax_url + "/"

        self.student_data_for_location = instance_state.get('student_data_for_location', {})
        self.max_grade = instance_state.get('max_grade', MAX_SCORE)
        if not isinstance(self.max_grade, (int, long)):
            #This could result in an exception, but not wrapping in a try catch block so it moves up the stack
            self.max_grade = int(self.max_grade)

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
        if not self.use_for_single_location:
            return self.peer_grading()
        else:
            return self.peer_grading_problem({'location' : self.link_to_location})['html']

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
            'save_calibration_essay' : self.save_calibration_essay,
            'problem' : self.peer_grading_problem,
            }

        if dispatch not in handlers:
            return 'Error'

        d = handlers[dispatch](get)

        return json.dumps(d, cls=ComplexEncoder)

    def query_data_for_location(self):
        student_id = self.system.anonymous_student_id
        location = self.system.location
        success = False
        response = {}

        try:
            response = self.peer_gs.get_data_for_location(location, student_id)
            count_graded = response['count_graded']
            count_required = response['count_required']
            success = True
        except GradingServiceError:
            log.exception("Error getting location data from controller for location {0}, student {1}"
            .format(location, student_id))

        return success, response

    def get_progress(self):
        pass

    def get_score(self):
        if not self.use_for_single_location or not self.is_graded:
            return None

        try:
            count_graded = self.student_data_for_location['count_graded']
            count_required = self.student_data_for_location['count_required']
        except:
            success, response = self.query_data_for_location()
            if not success:
                log.exception("No instance data found and could not get data from controller for loc {0} student {1}".format(
                    self.system.location, self.system.anonymous_student_id
                ))
                return None
            count_graded = response['count_graded']
            count_required = response['count_required']
            if count_required>0 and count_graded>=count_required:
                self.student_data_for_location = response

        score_dict = {
            'score': int(count_graded>=count_required),
            'total': self.max_grade,
            }

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
            return _err_response(message)
        grader_id = self.system.anonymous_student_id
        location = get['location']

        try:
            response = self.peer_gs.get_next_submission(location, grader_id)
            return response
        except GradingServiceError:
            log.exception("Error getting next submission.  server url: {0}  location: {1}, grader_id: {2}"
            .format(self.peer_gs.url, location, grader_id))
            return {'success': False,
                               'error': 'Could not connect to grading service'}

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

        required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback', 'rubric_scores[]', 'submission_flagged'])
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
            log.exception("""Error saving grade.  server url: {0}, location: {1}, submission_id:{2},
                            submission_key: {3}, score: {4}"""
            .format(self.peer_gs.url,
                location, submission_id, submission_key, score)
            )
            return {
                'success': False,
                'error': 'Could not connect to grading service'
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
            return _err_response(message)
        grader_id = self.system.anonymous_student_id

        location = get['location']

        try:
            response = self.peer_gs.is_student_calibrated(location, grader_id)
            return response
        except GradingServiceError:
            log.exception("Error from grading service.  server url: {0}, grader_id: {0}, location: {1}"
            .format(self.peer_gs.url, grader_id, location))
            return {
                'success': False,
                'error': 'Could not connect to grading service'
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
            return _err_response(message)

        grader_id = self.system.anonymous_student_id

        location = get['location']
        try:
            response = self.peer_gs.show_calibration_essay(location, grader_id)
            return response
        except GradingServiceError:
            log.exception("Error from grading service.  server url: {0}, location: {0}"
            .format(self.peer_gs.url, location))
            return {'success': False,
                               'error': 'Could not connect to grading service'}
        # if we can't parse the rubric into HTML,
        except etree.XMLSyntaxError:
            log.exception("Cannot parse rubric string. Raw string: {0}"
            .format(rubric))
            return {'success': False,
                               'error': 'Error displaying submission'}


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
            return _err_response(message)
        grader_id = self.system.anonymous_student_id

        location = get['location']
        calibration_essay_id = get['submission_id']
        submission_key = get['submission_key']
        score = get['score']
        feedback = get['feedback']
        rubric_scores = get['rubric_scores[]']

        try:
            response = self.peer_gs.save_calibration_essay(location, grader_id, calibration_essay_id,
                submission_key, score, feedback, rubric_scores)
            return response
        except GradingServiceError:
            log.exception("Error saving calibration grade, location: {0}, submission_id: {1}, submission_key: {2}, grader_id: {3}".format(location, submission_id, submission_key, grader_id))
            return _err_response('Could not connect to grading service')

    def peer_grading(self, get = None):
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
            error_text = "Error occured while contacting the grading service"
            success = False
        # catch error if if the json loads fails
        except ValueError:
            error_text = "Could not get problem list"
            success = False

        ajax_url = self.ajax_url
        html = self.system.render_template('peer_grading/peer_grading.html', {
            'course_id': self.system.course_id,
            'ajax_url': ajax_url,
            'success': success,
            'problem_list': problem_list,
            'error_text': error_text,
            # Checked above
            'staff_access': False,
            'use_single_location' : self.use_for_single_location,
            })

        return html

    def peer_grading_problem(self, get = None):
        '''
        Show individual problem interface
        '''
        if get == None or get.get('location')==None:
            if not self.use_for_single_location:
                #This is an error case, because it must be set to use a single location to be called without get parameters
                return {'html' : "", 'success' : False}
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
            'use_single_location' : self.use_for_single_location,
            })

        return {'html' : html, 'success' : True}

    def get_instance_state(self):
        """
        Returns the current instance state.  The module can be recreated from the instance state.
        Input: None
        Output: A dictionary containing the instance state.
        """

        state = {
            'student_data_for_location' : self.student_data_for_location,
            }

        return json.dumps(state)

class PeerGradingDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/html-edit.html"
    module_class = PeerGradingModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "peer_grading"

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the individual tasks, the rubric, and the prompt, and parse

        Returns:
        {
        'rubric': 'some-html',
        'prompt': 'some-html',
        'task_xml': dictionary of xml strings,
        }
        """
        log.debug("In definition")
        expected_children = []
        for child in expected_children:
            if len(xml_object.xpath(child)) == 0:
                raise ValueError("Peer grading definition must include at least one '{0}' tag".format(child))

        def parse_task(k):
            """Assumes that xml_object has child k"""
            return [stringify_children(xml_object.xpath(k)[i]) for i in xrange(0, len(xml_object.xpath(k)))]

        def parse(k):
            """Assumes that xml_object has child k"""
            return xml_object.xpath(k)[0]

        return {}


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('peergrading')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['task']:
            add_child(child)

        return elt