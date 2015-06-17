import json
import logging
from lxml import etree

from xmodule.capa_module import ComplexEncoder
from xmodule.progress import Progress
from xmodule.stringify import stringify_children
import openendedchild

from .combined_open_ended_rubric import CombinedOpenEndedRubric

log = logging.getLogger("edx.courseware")


class SelfAssessmentModule(openendedchild.OpenEndedChild):
    """
    A Self Assessment module that allows students to write open-ended responses,
    submit, then see a rubric and rate themselves.  Persists student supplied
    hints, answers, and assessment judgment (currently only correct/incorrect).
    Parses xml definition file--see below for exact format.

    Sample XML format:
    <selfassessment>
        <hintprompt>
            What hint about this problem would you give to someone?
        </hintprompt>
        <submitmessage>
            Save Succcesful.  Thanks for participating!
        </submitmessage>
    </selfassessment>
    """
    TEMPLATE_DIR = "combinedopenended/selfassessment"
    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    REQUEST_HINT = 'request_hint'
    DONE = 'done'

    def setup_response(self, system, location, definition, descriptor):
        """
        Sets up the module
        @param system: Modulesystem
        @param location: location, to let the module know where it is.
        @param definition: XML definition of the module.
        @param descriptor: SelfAssessmentDescriptor
        @return: None
        """
        self.child_prompt = stringify_children(self.child_prompt)
        self.child_rubric = stringify_children(self.child_rubric)

    def get_html(self, system):
        """
        Gets context and renders HTML that represents the module
        @param system: Modulesystem
        @return: Rendered HTML
        """
        # set context variables and render template
        previous_answer = self.get_display_answer()

        # Use the module name as a unique id to pass to the template.
        try:
            module_id = self.system.location.name
        except AttributeError:
            # In cases where we don't have a system or a location, use a fallback.
            module_id = "self_assessment"

        context = {
            'prompt': self.child_prompt,
            'previous_answer': previous_answer,
            'ajax_url': system.ajax_url,
            'initial_rubric': self.get_rubric_html(system),
            'state': self.child_state,
            'allow_reset': self._allow_reset(),
            'child_type': 'selfassessment',
            'accept_file_upload': self.accept_file_upload,
            'module_id': module_id,
        }

        html = system.render_template('{0}/self_assessment_prompt.html'.format(self.TEMPLATE_DIR), context)
        return html

    def handle_ajax(self, dispatch, data, system):
        """
        This is called by courseware.module_render, to handle an AJAX call.
        "data" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
        'progress': 'none'/'in_progress'/'done',
        <other request-specific values here > }
        """

        handlers = {
            'save_answer': self.save_answer,
            'save_assessment': self.save_assessment,
            'save_post_assessment': self.save_hint,
            'store_answer': self.store_answer,
        }

        if dispatch not in handlers:
            # This is a dev_facing_error
            log.error("Cannot find {0} in handlers in handle_ajax function for open_ended_module.py".format(dispatch))
            # This is a dev_facing_error
            return json.dumps({'error': 'Error handling action.  Please try again.', 'success': False})

        before = self.get_progress()
        d = handlers[dispatch](data, system)
        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
        })
        return json.dumps(d, cls=ComplexEncoder)

    def get_rubric_html(self, system):
        """
        Return the appropriate version of the rubric, based on the state.
        """
        if self.child_state == self.INITIAL:
            return ''

        rubric_renderer = CombinedOpenEndedRubric(system.render_template, False)
        rubric_dict = rubric_renderer.render_rubric(self.child_rubric)
        success = rubric_dict['success']
        rubric_html = rubric_dict['html']

        # we'll render it
        context = {
            'rubric': rubric_html,
            'max_score': self._max_score,
        }

        if self.child_state == self.ASSESSING:
            context['read_only'] = False
        elif self.child_state in (self.POST_ASSESSMENT, self.DONE):
            context['read_only'] = True
        else:
            # This is a dev_facing_error
            raise ValueError("Self assessment module is in an illegal state '{0}'".format(self.child_state))

        return system.render_template('{0}/self_assessment_rubric.html'.format(self.TEMPLATE_DIR), context)

    def get_hint_html(self, system):
        """
        Return the appropriate version of the hint view, based on state.
        """
        if self.child_state in (self.INITIAL, self.ASSESSING):
            return ''

        if self.child_state == self.DONE:
            # display the previous hint
            latest = self.latest_post_assessment(system)
            hint = latest if latest is not None else ''
        else:
            hint = ''

        context = {'hint': hint}

        if self.child_state == self.POST_ASSESSMENT:
            context['read_only'] = False
        elif self.child_state == self.DONE:
            context['read_only'] = True
        else:
            # This is a dev_facing_error
            raise ValueError("Self Assessment module is in an illegal state '{0}'".format(self.child_state))

        return system.render_template('{0}/self_assessment_hint.html'.format(self.TEMPLATE_DIR), context)

    def save_answer(self, data, system):
        """
        After the answer is submitted, show the rubric.

        Args:
            data: the request dictionary passed to the ajax request.  Should contain
                a key 'student_answer'

        Returns:
            Dictionary with keys 'success' and either 'error' (if not success),
            or 'rubric_html' (if success).
        """
        # Check to see if this problem is closed
        closed, msg = self.check_if_closed()
        if closed:
            return msg

        if self.child_state != self.INITIAL:
            return self.out_of_sync_error(data)

        error_message = ""
        # add new history element with answer and empty score and hint.
        success, error_message, data = self.append_file_link_to_student_answer(data)
        if success:
            data['student_answer'] = SelfAssessmentModule.sanitize_html(data['student_answer'])
            self.new_history_entry(data['student_answer'])
            self.change_state(self.ASSESSING)

        return {
            'success': success,
            'rubric_html': self.get_rubric_html(system),
            'error': error_message,
            'student_response': data['student_answer'].replace("\n", "<br/>"),
        }

    def save_assessment(self, data, _system):
        """
        Save the assessment.  If the student said they're right, don't ask for a
        hint, and go straight to the done state.  Otherwise, do ask for a hint.

        Returns a dict { 'success': bool, 'state': state,

        'hint_html': hint_html OR 'message_html': html and 'allow_reset',

           'error': error-msg},

        with 'error' only present if 'success' is False, and 'hint_html' or
        'message_html' only if success is true

        :param data: A `webob.multidict.MultiDict` containing the keys
            asasssment: The sum of assessment scores
            score_list[]: A multivalue key containing all the individual scores
        """

        closed, msg = self.check_if_closed()
        if closed:
            return msg

        if self.child_state != self.ASSESSING:
            return self.out_of_sync_error(data)

        try:
            score = int(data.get('assessment'))
            score_list = [int(x) for x in data.getall('score_list[]')]
        except (ValueError, TypeError):
            # This is a dev_facing_error
            log.error("Non-integer score value passed to save_assessment, or no score list present.")
            # This is a student_facing_error
            _ = self.system.service(self, "i18n").ugettext
            return {
                'success': False,
                'error': _("Error saving your score.  Please notify course staff.")
            }

        # Record score as assessment and rubric scores as post assessment
        self.record_latest_score(score)
        self.record_latest_post_assessment(json.dumps(score_list))

        d = {'success': True, }

        self.change_state(self.DONE)
        d['allow_reset'] = self._allow_reset()

        d['state'] = self.child_state
        return d

    def save_hint(self, data, _system):
        '''
        Not used currently, as hints have been removed from the system.
        Save the hint.
        Returns a dict { 'success': bool,
                         'message_html': message_html,
                         'error': error-msg,
                         'allow_reset': bool},
        with the error key only present if success is False and message_html
        only if True.
        '''
        if self.child_state != self.POST_ASSESSMENT:
            # Note: because we only ask for hints on wrong answers, may not have
            # the same number of hints and answers.
            return self.out_of_sync_error(data)

        self.record_latest_post_assessment(data['hint'])
        self.change_state(self.DONE)

        return {
            'success': True,
            'message_html': '',
            'allow_reset': self._allow_reset(),
        }

    def latest_post_assessment(self, system):
        latest_post_assessment = super(SelfAssessmentModule, self).latest_post_assessment(system)
        try:
            rubric_scores = json.loads(latest_post_assessment)
        except:
            rubric_scores = []
        return [rubric_scores]


class SelfAssessmentDescriptor(object):
    """
    Module for adding self assessment questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = SelfAssessmentModule
    filename_extension = "xml"

    has_score = True

    def __init__(self, system):
        self.system = system

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the rubric, prompt, and submitmessage into a dictionary.

        Returns:
        {
        'submitmessage': 'some-html'
        'hintprompt': 'some-html'
        }
        """
        expected_children = []
        for child in expected_children:
            if len(xml_object.xpath(child)) != 1:
                # This is a staff_facing_error
                raise ValueError(
                    u"Self assessment definition must include exactly one '{0}' tag. Contact the learning sciences group for assistance.".format(
                        child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])

        return {}

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('selfassessment')

        def add_child(k):
            child_str = u'<{tag}>{body}</{tag}>'.format(tag=k, body=getattr(self, k))
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in []:
            add_child(child)

        return elt
