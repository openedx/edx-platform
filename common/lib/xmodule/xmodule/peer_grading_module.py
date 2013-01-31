"""
This module provides an interface on the grading-service backend
for peer grading

Use peer_grading_service() to get the version specified
in settings.PEER_GRADING_INTERFACE

"""
import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

from django.conf import settings
from django.http import HttpResponse, Http404
from grading_service import GradingService
from grading_service import GradingServiceError

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor
from xmodule.combined_open_ended_rubric import CombinedOpenEndedRubric
from student.models import unique_id_for_user
from lxml import etree

import copy
from fs.errors import ResourceNotFoundError
import itertools
import json
import logging
from lxml import etree
from lxml.html import rewrite_links
from path import path
import os
import sys

from pkg_resources import resource_string
from .capa_module import only_one, ComplexEncoder

from peer_grading_service import peer_grading_service

log = logging.getLogger(__name__)

class PeerGradingModule(XModule):
    _VERSION = 1

    js = {'coffee': [resource_string(__name__, 'js/src/combinedopenended/display.coffee'),
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
        self.peer_gs = peer_grading_service()
        log.debug(self.system)

    def _err_response(self, msg):
        """
        Return a HttpResponse with a json dump with success=False, and the given error message.
        """
        return HttpResponse(json.dumps({'success': False, 'error': msg}),
            mimetype="application/json")

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
        pass

    def handle_ajax(self, dispatch, get):
        """
        Needs to be implemented by child modules.  Handles AJAX events.
        @return:
        """

        handlers = {
            'get_next_submission': self.get_next_submission,
            'show_calibration_essay': self.show_calibration_essay,
            'save_post_assessment': self.message_post,
            'is_student_calibrated': self.is_student_calibrated,
            'save_grade': self.save_grade,
            'save_calibration_essay' : self.save_calibration_essay,
            }

        if dispatch not in handlers:
            return 'Error'

        before = self.get_progress()
        d = handlers[dispatch](get)
        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
            })
        return json.dumps(d, cls=ComplexEncoder)

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
        _check_post(request)
        required = set(['location'])
        success, message = _check_required(request, required)
        if not success:
            return _err_response(message)
        grader_id = unique_id_for_user(request.user)
        p = request.POST
        location = p['location']

        try:
            response = peer_grading_service().get_next_submission(location, grader_id)
            return HttpResponse(response,
                mimetype="application/json")
        except GradingServiceError:
            log.exception("Error getting next submission.  server url: {0}  location: {1}, grader_id: {2}"
            .format(peer_grading_service().url, location, grader_id))
            return json.dumps({'success': False,
                               'error': 'Could not connect to grading service'})

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
        _check_post(request)
        required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback', 'rubric_scores[]', 'submission_flagged'])
        success, message = _check_required(request, required)
        if not success:
            return _err_response(message)
        grader_id = unique_id_for_user(request.user)
        p = request.POST
        location = p['location']
        submission_id = p['submission_id']
        score = p['score']
        feedback = p['feedback']
        submission_key = p['submission_key']
        rubric_scores = p.getlist('rubric_scores[]')
        submission_flagged = p['submission_flagged']
        try:
            response = peer_grading_service().save_grade(location, grader_id, submission_id,
                score, feedback, submission_key, rubric_scores, submission_flagged)
            return HttpResponse(response, mimetype="application/json")
        except GradingServiceError:
            log.exception("""Error saving grade.  server url: {0}, location: {1}, submission_id:{2},
                            submission_key: {3}, score: {4}"""
            .format(peer_grading_service().url,
                location, submission_id, submission_key, score)
            )
            return json.dumps({'success': False,
                               'error': 'Could not connect to grading service'})



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
        _check_post(request)
        required = set(['location'])
        success, message = _check_required(request, required)
        if not success:
            return _err_response(message)
        grader_id = unique_id_for_user(request.user)
        p = request.POST
        location = p['location']

        try:
            response = peer_grading_service().is_student_calibrated(location, grader_id)
            return HttpResponse(response, mimetype="application/json")
        except GradingServiceError:
            log.exception("Error from grading service.  server url: {0}, grader_id: {0}, location: {1}"
            .format(peer_grading_service().url, grader_id, location))
            return json.dumps({'success': False,
                               'error': 'Could not connect to grading service'})



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
        _check_post(request)

        required = set(['location'])
        success, message = _check_required(request, required)
        if not success:
            return _err_response(message)

        grader_id = unique_id_for_user(request.user)
        p = request.POST
        location = p['location']
        try:
            response = peer_grading_service().show_calibration_essay(location, grader_id)
            return HttpResponse(response, mimetype="application/json")
        except GradingServiceError:
            log.exception("Error from grading service.  server url: {0}, location: {0}"
            .format(peer_grading_service().url, location))
            return json.dumps({'success': False,
                               'error': 'Could not connect to grading service'})
        # if we can't parse the rubric into HTML,
        except etree.XMLSyntaxError:
            log.exception("Cannot parse rubric string. Raw string: {0}"
            .format(rubric))
            return json.dumps({'success': False,
                               'error': 'Error displaying submission'})


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
        _check_post(request)

        required = set(['location', 'submission_id', 'submission_key', 'score', 'feedback', 'rubric_scores[]'])
        success, message = _check_required(request, required)
        if not success:
            return _err_response(message)
        grader_id = unique_id_for_user(request.user)
        p = request.POST
        location = p['location']
        calibration_essay_id = p['submission_id']
        submission_key = p['submission_key']
        score = p['score']
        feedback = p['feedback']
        rubric_scores = p.getlist('rubric_scores[]')

        try:
            response = peer_grading_service().save_calibration_essay(location, grader_id, calibration_essay_id,
                submission_key, score, feedback, rubric_scores)
            return HttpResponse(response, mimetype="application/json")
        except GradingServiceError:
            log.exception("Error saving calibration grade, location: {0}, submission_id: {1}, submission_key: {2}, grader_id: {3}".format(location, submission_id, submission_key, grader_id))
            return _err_response('Could not connect to grading service')
    def peer_grading(self, request, course_id):
        '''
        Show a peer grading interface
        '''

        # call problem list service
        success = False
        error_text = ""
        problem_list = []
        try:
            problem_list_json = self.peer_gs.get_problem_list(course_id, unique_id_for_user(request.user))
            problem_list_dict = json.loads(problem_list_json)
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

        ajax_url = _reverse_with_slash('peer_grading', course_id)

        return self.system.render_template('peer_grading/peer_grading.html', {
            'course': course,
            'course_id': course_id,
            'ajax_url': ajax_url,
            'success': success,
            'problem_list': problem_list,
            'error_text': error_text,
            # Checked above
            'staff_access': False, })


    def peer_grading_problem(request, course_id):
        '''
        Show individual problem interface
        '''
        course = get_course_with_access(request.user, course_id, 'load')
        problem_location = request.GET.get("location")

        ajax_url = _reverse_with_slash('peer_grading', course_id)

        return render_to_response('peer_grading/peer_grading_problem.html', {
            'view_html': '',
            'course': course,
            'problem_location': problem_location,
            'course_id': course_id,
            'ajax_url': ajax_url,
            # Checked above
            'staff_access': False, })

class PeerGradingDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/html-edit.html"
    module_class = CombinedOpenEndedModule
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