#
# File:   courseware/capa/responsetypes.py
#
'''
Problem response evaluation.  Handles checking of student responses,
of a variety of types.

Used by capa_problem.py
'''

# standard library imports
import abc
import cgi
import inspect
import json
import logging
import numbers
import numpy
import os
import sys
import random
import re
import requests
import subprocess
import textwrap
import traceback
import xml.sax.saxutils as saxutils

from collections import namedtuple
from shapely.geometry import Point, MultiPoint

# specific library imports
from calc import evaluator, UndefinedVariable
from . import correctmap
from datetime import datetime
from pytz import UTC
from .util import *
from lxml import etree
from lxml.html.soupparser import fromstring as fromstring_bs     # uses Beautiful Soup!!! FIXME?
import capa.xqueue_interface as xqueue_interface

import safe_exec

log = logging.getLogger(__name__)


CorrectMap = correctmap.CorrectMap
CORRECTMAP_PY = None


#-----------------------------------------------------------------------------
# Exceptions


class LoncapaProblemError(Exception):
    '''
    Error in specification of a problem
    '''
    pass


class ResponseError(Exception):
    '''
    Error for failure in processing a response, including
    exceptions that occur when executing a custom script.
    '''
    pass


class StudentInputError(Exception):
    '''
    Error for an invalid student input.
    For example, submitting a string when the problem expects a number
    '''
    pass

#-----------------------------------------------------------------------------
#
# Main base class for CAPA responsetypes


class LoncapaResponse(object):
    """
    Base class for CAPA responsetypes.  Each response type (ie a capa question,
    which is part of a capa problem) is represented as a subclass,
    which should provide the following methods:

      - get_score           : evaluate the given student answers, and return a CorrectMap
      - get_answers         : provide a dict of the expected answers for this problem

    Each subclass must also define the following attributes:

      - response_tag         : xhtml tag identifying this response (used in auto-registering)

    In addition, these methods are optional:

      - setup_response : find and note the answer input field IDs for the response; called
                         by __init__

      - check_hint_condition : check to see if the student's answers satisfy a particular
                               condition for a hint to be displayed

      - render_html          : render this Response as HTML (must return XHTML-compliant string)
      - __unicode__          : unicode representation of this Response

    Each response type may also specify the following attributes:

      - max_inputfields      : (int) maximum number of answer input fields (checked in __init__
                               if not None)

      - allowed_inputfields  : list of allowed input fields (each a string) for this Response

      - required_attributes  : list of required attributes (each a string) on the main
                               response XML stanza

      - hint_tag             : xhtml tag identifying hint associated with this response inside
                               hintgroup
    """
    __metaclass__ = abc.ABCMeta  # abc = Abstract Base Class

    response_tag = None
    hint_tag = None

    max_inputfields = None
    allowed_inputfields = []
    required_attributes = []

    def __init__(self, xml, inputfields, context, system=None):
        '''
        Init is passed the following arguments:

          - xml         : ElementTree of this Response
          - inputfields : ordered list of ElementTrees for each input entry field in this Response
          - context     : script processor context
          - system      : ModuleSystem instance which provides OS, rendering, and user context

        '''
        self.xml = xml
        self.inputfields = inputfields
        self.context = context
        self.system = system

        self.id = xml.get('id')

        for abox in inputfields:
            if abox.tag not in self.allowed_inputfields:
                msg = "%s: cannot have input field %s" % (
                    unicode(self), abox.tag)
                msg += "\nSee XML source line %s" % getattr(
                    xml, 'sourceline', '<unavailable>')
                raise LoncapaProblemError(msg)

        if self.max_inputfields and len(inputfields) > self.max_inputfields:
            msg = "%s: cannot have more than %s input fields" % (
                unicode(self), self.max_inputfields)
            msg += "\nSee XML source line %s" % getattr(
                xml, 'sourceline', '<unavailable>')
            raise LoncapaProblemError(msg)

        for prop in self.required_attributes:
            if not xml.get(prop):
                msg = "Error in problem specification: %s missing required attribute %s" % (
                    unicode(self), prop)
                msg += "\nSee XML source line %s" % getattr(
                    xml, 'sourceline', '<unavailable>')
                raise LoncapaProblemError(msg)

        # ordered list of answer_id values for this response
        self.answer_ids = [x.get('id') for x in self.inputfields]
        if self.max_inputfields == 1:
            # for convenience
            self.answer_id = self.answer_ids[0]

        # map input_id -> maxpoints
        self.maxpoints = dict()
        for inputfield in self.inputfields:
            # By default, each answerfield is worth 1 point
            maxpoints = inputfield.get('points', '1')
            self.maxpoints.update({inputfield.get('id'): int(maxpoints)})

        # dict for default answer map (provided in input elements)
        self.default_answer_map = {}
        for entry in self.inputfields:
            answer = entry.get('correct_answer')
            if answer:
                self.default_answer_map[entry.get(
                    'id')] = contextualize_text(answer, self.context)

        if hasattr(self, 'setup_response'):
            self.setup_response()

    def get_max_score(self):
        '''
        Return the total maximum points of all answer fields under this Response
        '''
        return sum(self.maxpoints.values())

    def render_html(self, renderer, response_msg=''):
        '''
        Return XHTML Element tree representation of this Response.

        Arguments:

          - renderer : procedure which produces HTML given an ElementTree
          - response_msg: a message displayed at the end of the Response
        '''
        # render ourself as a <span> + our content
        tree = etree.Element('span')

        # problem author can make this span display:inline
        if self.xml.get('inline', ''):
            tree.set('class', 'inline')

        for item in self.xml:
            # call provided procedure to do the rendering
            item_xhtml = renderer(item)
            if item_xhtml is not None:
                tree.append(item_xhtml)
        tree.tail = self.xml.tail

        # Add a <div> for the message at the end of the response
        if response_msg:
            tree.append(self._render_response_msg_html(response_msg))

        return tree

    def evaluate_answers(self, student_answers, old_cmap):
        '''
        Called by capa_problem.LoncapaProblem to evaluate student answers, and to
        generate hints (if any).

        Returns the new CorrectMap, with (correctness,msg,hint,hintmode) for each answer_id.
        '''
        new_cmap = self.get_score(student_answers)
        self.get_hints(convert_files_to_filenames(
            student_answers), new_cmap, old_cmap)
        # log.debug('new_cmap = %s' % new_cmap)
        return new_cmap

    def get_hints(self, student_answers, new_cmap, old_cmap):
        '''
        Generate adaptive hints for this problem based on student answers, the old CorrectMap,
        and the new CorrectMap produced by get_score.

        Does not return anything.

        Modifies new_cmap, by adding hints to answer_id entries as appropriate.
        '''
        hintgroup = self.xml.find('hintgroup')
        if hintgroup is None:
            return

        # hint specified by function?
        hintfn = hintgroup.get('hintfn')
        if hintfn:
            # Hint is determined by a function defined in the <script> context; evaluate
            # that function to obtain list of hint, hintmode for each answer_id.

            # The function should take arguments (answer_ids, student_answers, new_cmap, old_cmap)
            # and it should modify new_cmap as appropriate.

            # We may extend this in the future to add another argument which provides a
            # callback procedure to a social hint generation system.

            global CORRECTMAP_PY
            if CORRECTMAP_PY is None:
                # We need the CorrectMap code for hint functions. No, this is not great.
                CORRECTMAP_PY = inspect.getsource(correctmap)

            code = (
                CORRECTMAP_PY + "\n" +
                self.context['script_code'] + "\n" +
                textwrap.dedent("""
                    new_cmap = CorrectMap()
                    new_cmap.set_dict(new_cmap_dict)
                    old_cmap = CorrectMap()
                    old_cmap.set_dict(old_cmap_dict)
                    {hintfn}(answer_ids, student_answers, new_cmap, old_cmap)
                    new_cmap_dict.update(new_cmap.get_dict())
                    old_cmap_dict.update(old_cmap.get_dict())
                    """).format(hintfn=hintfn)
            )
            globals_dict = {
                'answer_ids': self.answer_ids,
                'student_answers': student_answers,
                'new_cmap_dict': new_cmap.get_dict(),
                'old_cmap_dict': old_cmap.get_dict(),
            }

            try:
                safe_exec.safe_exec(
                    code,
                    globals_dict,
                    python_path=self.context['python_path'],
                    slug=self.id,
                    random_seed=self.context['seed'],
                    unsafely=self.system.can_execute_unsafe_code(),
                )
            except Exception as err:
                msg = 'Error %s in evaluating hint function %s' % (err, hintfn)
                msg += "\nSee XML source line %s" % getattr(
                    self.xml, 'sourceline', '<unavailable>')
                raise ResponseError(msg)

            new_cmap.set_dict(globals_dict['new_cmap_dict'])
            return

        # hint specified by conditions and text dependent on conditions (a-la Loncapa design)
        # see http://help.loncapa.org/cgi-bin/fom?file=291
        #
        # Example:
        #
        # <formularesponse samples="x@-5:5#11" id="11" answer="$answer">
        #   <textline size="25" />
        #   <hintgroup>
        #     <formulahint samples="x@-5:5#11" answer="$wrongans" name="inversegrad"></formulahint>
        #     <hintpart on="inversegrad">
        #       <text>You have inverted the slope in the question.  The slope is
        #             (y2-y1)/(x2 - x1) you have the slope as (x2-x1)/(y2-y1).</text>
        #     </hintpart>
        #   </hintgroup>
        # </formularesponse>

        if (self.hint_tag is not None
            and hintgroup.find(self.hint_tag) is not None
                and hasattr(self, 'check_hint_condition')):

            rephints = hintgroup.findall(self.hint_tag)
            hints_to_show = self.check_hint_condition(
                rephints, student_answers)

            # can be 'on_request' or 'always' (default)
            hintmode = hintgroup.get('mode', 'always')
            for hintpart in hintgroup.findall('hintpart'):
                if hintpart.get('on') in hints_to_show:
                    hint_text = hintpart.find('text').text
                    # make the hint appear after the last answer box in this
                    # response
                    aid = self.answer_ids[-1]
                    new_cmap.set_hint_and_mode(aid, hint_text, hintmode)
            log.debug('after hint: new_cmap = %s', new_cmap)

    @abc.abstractmethod
    def get_score(self, student_answers):
        '''
        Return a CorrectMap for the answers expected vs given.  This includes
        (correctness, npoints, msg) for each answer_id.

        Arguments:
         - student_answers : dict of (answer_id, answer) where answer = student input (string)
        '''
        pass

    @abc.abstractmethod
    def get_answers(self):
        '''
        Return a dict of (answer_id, answer_text) for each answer for this question.
        '''
        pass

    def check_hint_condition(self, hxml_set, student_answers):
        '''
        Return a list of hints to show.

          - hxml_set        : list of Element trees, each specifying a condition to be
                              satisfied for a named hint condition

          - student_answers : dict of student answers

        Returns a list of names of hint conditions which were satisfied.  Those are used
        to determine which hints are displayed.
        '''
        pass

    def setup_response(self):
        pass

    def __unicode__(self):
        return u'LoncapaProblem Response %s' % self.xml.tag

    def _render_response_msg_html(self, response_msg):
        """ Render a <div> for a message that applies to the entire response.

        *response_msg* is a string, which may contain XHTML markup

        Returns an etree element representing the response message <div> """
        # First try wrapping the text in a <div> and parsing
        # it as an XHTML tree
        try:
            response_msg_div = etree.XML('<div>%s</div>' % str(response_msg))

        # If we can't do that, create the <div> and set the message
        # as the text of the <div>
        except:
            response_msg_div = etree.Element('div')
            response_msg_div.text = str(response_msg)

        # Set the css class of the message <div>
        response_msg_div.set("class", "response_message")

        return response_msg_div


#-----------------------------------------------------------------------------

class JavascriptResponse(LoncapaResponse):
    """
    This response type is used when the student's answer is graded via
    Javascript using Node.js.
    """

    response_tag = 'javascriptresponse'
    max_inputfields = 1
    allowed_inputfields = ['javascriptinput']

    def setup_response(self):

        # Sets up generator, grader, display, and their dependencies.
        self.parse_xml()

        self.compile_display_javascript()

        self.params = self.extract_params()

        if self.generator:
            self.problem_state = self.generate_problem_state()
        else:
            self.problem_state = None

        self.solution = None

        self.prepare_inputfield()

    def compile_display_javascript(self):

        # TODO FIXME
        # arjun: removing this behavior for now (and likely forever). Keeping
        # until we decide on exactly how to solve this issue. For now, files are
        # manually being compiled to DATA_DIR/js/compiled.

        # latestTimestamp = 0
        # basepath = self.system.filestore.root_path + '/js/'
        # for filename in (self.display_dependencies + [self.display]):
        #    filepath = basepath + filename
        #    timestamp = os.stat(filepath).st_mtime
        #    if timestamp > latestTimestamp:
        #        latestTimestamp = timestamp
        #
        # h = hashlib.md5()
        # h.update(self.answer_id + str(self.display_dependencies))
        # compiled_filename = 'compiled/' + h.hexdigest() + '.js'
        # compiled_filepath = basepath + compiled_filename

        # if not os.path.exists(compiled_filepath) or os.stat(compiled_filepath).st_mtime < latestTimestamp:
        #    outfile = open(compiled_filepath, 'w')
        #    for filename in (self.display_dependencies + [self.display]):
        #        filepath = basepath + filename
        #        infile = open(filepath, 'r')
        #        outfile.write(infile.read())
        #        outfile.write(';\n')
        #        infile.close()
        #    outfile.close()

        # TODO this should also be fixed when the above is fixed.
        filename = self.system.ajax_url.split('/')[-1] + '.js'
        self.display_filename = 'compiled/' + filename

    def parse_xml(self):
        self.generator_xml = self.xml.xpath('//*[@id=$id]//generator',
                                            id=self.xml.get('id'))[0]

        self.grader_xml = self.xml.xpath('//*[@id=$id]//grader',
                                         id=self.xml.get('id'))[0]

        self.display_xml = self.xml.xpath('//*[@id=$id]//display',
                                          id=self.xml.get('id'))[0]

        self.xml.remove(self.generator_xml)
        self.xml.remove(self.grader_xml)
        self.xml.remove(self.display_xml)

        self.generator = self.generator_xml.get("src")
        self.grader = self.grader_xml.get("src")
        self.display = self.display_xml.get("src")

        if self.generator_xml.get("dependencies"):
            self.generator_dependencies = self.generator_xml.get(
                "dependencies").split()
        else:
            self.generator_dependencies = []

        if self.grader_xml.get("dependencies"):
            self.grader_dependencies = self.grader_xml.get(
                "dependencies").split()
        else:
            self.grader_dependencies = []

        if self.display_xml.get("dependencies"):
            self.display_dependencies = self.display_xml.get(
                "dependencies").split()
        else:
            self.display_dependencies = []

        self.display_class = self.display_xml.get("class")

    def get_node_env(self):

        js_dir = os.path.join(self.system.filestore.root_path, 'js')
        tmp_env = os.environ.copy()
        node_path = self.system.node_path + ":" + os.path.normpath(js_dir)
        tmp_env["NODE_PATH"] = node_path
        return tmp_env

    def call_node(self, args):
        # Node.js code is un-sandboxed. If the XModuleSystem says we aren't
        # allowed to run unsafe code, then stop now.
        if not self.system.can_execute_unsafe_code():
            raise LoncapaProblemError("Execution of unsafe Javascript code is not allowed.")

        subprocess_args = ["node"]
        subprocess_args.extend(args)

        return subprocess.check_output(subprocess_args, env=self.get_node_env())

    def generate_problem_state(self):

        generator_file = os.path.dirname(os.path.normpath(
            __file__)) + '/javascript_problem_generator.js'
        output = self.call_node([generator_file,
                                 self.generator,
                                 json.dumps(self.generator_dependencies),
                                 json.dumps(str(self.context['seed'])),
                                 json.dumps(self.params)]).strip()

        return json.loads(output)

    def extract_params(self):

        params = {}

        for param in self.xml.xpath('//*[@id=$id]//responseparam',
                                    id=self.xml.get('id')):

            raw_param = param.get("value")
            params[param.get("name")] = json.loads(
                contextualize_text(raw_param, self.context))

        return params

    def prepare_inputfield(self):

        for inputfield in self.xml.xpath('//*[@id=$id]//javascriptinput',
                                         id=self.xml.get('id')):

            escapedict = {'"': '&quot;'}

            encoded_params = json.dumps(self.params)
            encoded_params = saxutils.escape(encoded_params, escapedict)
            inputfield.set("params", encoded_params)

            encoded_problem_state = json.dumps(self.problem_state)
            encoded_problem_state = saxutils.escape(encoded_problem_state,
                                                    escapedict)
            inputfield.set("problem_state", encoded_problem_state)

            inputfield.set("display_file", self.display_filename)
            inputfield.set("display_class", self.display_class)

    def get_score(self, student_answers):
        json_submission = student_answers[self.answer_id]
        (all_correct, evaluation, solution) = self.run_grader(json_submission)
        self.solution = solution
        correctness = 'correct' if all_correct else 'incorrect'
        if all_correct:
            points = self.get_max_score()
        else:
            points = 0
        return CorrectMap(self.answer_id, correctness, npoints=points, msg=evaluation)

    def run_grader(self, submission):
        if submission is None or submission == '':
            submission = json.dumps(None)

        grader_file = os.path.dirname(os.path.normpath(
            __file__)) + '/javascript_problem_grader.js'
        outputs = self.call_node([grader_file,
                                  self.grader,
                                  json.dumps(self.grader_dependencies),
                                  submission,
                                  json.dumps(self.problem_state),
                                  json.dumps(self.params)]).split('\n')

        all_correct = json.loads(outputs[0].strip())
        evaluation = outputs[1].strip()
        solution = outputs[2].strip()
        return (all_correct, evaluation, solution)

    def get_answers(self):
        if self.solution is None:
            (_, _, self.solution) = self.run_grader(None)

        return {self.answer_id: self.solution}


#-----------------------------------------------------------------------------
class ChoiceResponse(LoncapaResponse):
    """
    This response type is used when the student chooses from a discrete set of
    choices. Currently, to be marked correct, all "correct" choices must be
    supplied by the student, and no extraneous choices may be included.

    This response type allows for two inputtypes: radiogroups and checkbox
    groups. radiogroups are used when the student should select a single answer,
    and checkbox groups are used when the student may supply 0+ answers.
    Note: it is suggested to include a "None of the above" choice when no
    answer is correct for a checkboxgroup inputtype; this ensures that a student
    must actively mark something to get credit.

    If two choices are marked as correct with a radiogroup, the student will
    have no way to get the answer right.

    TODO: Allow for marking choices as 'optional' and 'required', which would
    not penalize a student for including optional answers and would also allow
    for questions in which the student can supply one out of a set of correct
    answers.This would also allow for survey-style questions in which all
    answers are correct.

    Example:

    <choiceresponse>
        <radiogroup>
            <choice correct="false">
                <text>This is a wrong answer.</text>
            </choice>
            <choice correct="true">
                <text>This is the right answer.</text>
            </choice>
            <choice correct="false">
                <text>This is another wrong answer.</text>
            </choice>
        </radiogroup>
    </choiceresponse>

    In the above example, radiogroup can be replaced with checkboxgroup to allow
    the student to select more than one choice.

    TODO: In order for the inputtypes to render properly, this response type
    must run setup_response prior to the input type rendering. Specifically, the
    choices must be given names. This behavior seems like a leaky abstraction,
    and it'd be nice to change this at some point.

    """

    response_tag = 'choiceresponse'
    max_inputfields = 1
    allowed_inputfields = ['checkboxgroup', 'radiogroup']

    def setup_response(self):

        self.assign_choice_names()

        correct_xml = self.xml.xpath('//*[@id=$id]//choice[@correct="true"]',
                                     id=self.xml.get('id'))

        self.correct_choices = set([choice.get(
            'name') for choice in correct_xml])

    def assign_choice_names(self):
        '''
        Initialize name attributes in <choice> tags for this response.
        '''

        for index, choice in enumerate(self.xml.xpath('//*[@id=$id]//choice',
                                                      id=self.xml.get('id'))):
            choice.set("name", "choice_" + str(index))

    def get_score(self, student_answers):

        student_answer = student_answers.get(self.answer_id, [])

        if not isinstance(student_answer, list):
            student_answer = [student_answer]

        student_answer = set(student_answer)

        required_selected = len(self.correct_choices - student_answer) == 0
        no_extra_selected = len(student_answer - self.correct_choices) == 0

        correct = required_selected & no_extra_selected

        if correct:
            return CorrectMap(self.answer_id, 'correct')
        else:
            return CorrectMap(self.answer_id, 'incorrect')

    def get_answers(self):
        return {self.answer_id: list(self.correct_choices)}

#-----------------------------------------------------------------------------


class MultipleChoiceResponse(LoncapaResponse):
    # TODO: handle direction and randomize

    response_tag = 'multiplechoiceresponse'
    max_inputfields = 1
    allowed_inputfields = ['choicegroup']

    def setup_response(self):
        # call secondary setup for MultipleChoice questions, to set name
        # attributes
        self.mc_setup_response()

        # define correct choices (after calling secondary setup)
        xml = self.xml
        cxml = xml.xpath('//*[@id=$id]//choice', id=xml.get('id'))

        # contextualize correct attribute and then select ones for which
        # correct = "true"
        self.correct_choices = [
            contextualize_text(choice.get('name'), self.context)
            for choice in cxml
            if contextualize_text(choice.get('correct'), self.context) == "true"]

    def mc_setup_response(self):
        '''
        Initialize name attributes in <choice> stanzas in the <choicegroup> in this response.
        '''
        i = 0
        for response in self.xml.xpath("choicegroup"):
            rtype = response.get('type')
            if rtype not in ["MultipleChoice"]:
                # force choicegroup to be MultipleChoice if not valid
                response.set("type", "MultipleChoice")
            for choice in list(response):
                if choice.get("name") is None:
                    choice.set("name", "choice_" + str(i))
                    i += 1
                else:
                    choice.set("name", "choice_" + choice.get("name"))

    def get_score(self, student_answers):
        '''
        grade student response.
        '''
        # log.debug('%s: student_answers=%s, correct_choices=%s' % (
        #   unicode(self), student_answers, self.correct_choices))
        if (self.answer_id in student_answers
                and student_answers[self.answer_id] in self.correct_choices):
            return CorrectMap(self.answer_id, 'correct')
        else:
            return CorrectMap(self.answer_id, 'incorrect')

    def get_answers(self):
        return {self.answer_id: self.correct_choices}


class TrueFalseResponse(MultipleChoiceResponse):

    response_tag = 'truefalseresponse'

    def mc_setup_response(self):
        i = 0
        for response in self.xml.xpath("choicegroup"):
            response.set("type", "TrueFalse")
            for choice in list(response):
                if choice.get("name") is None:
                    choice.set("name", "choice_" + str(i))
                    i += 1
                else:
                    choice.set("name", "choice_" + choice.get("name"))

    def get_score(self, student_answers):
        correct = set(self.correct_choices)
        answers = set(student_answers.get(self.answer_id, []))

        if correct == answers:
            return CorrectMap(self.answer_id, 'correct')

        return CorrectMap(self.answer_id, 'incorrect')

#-----------------------------------------------------------------------------


class OptionResponse(LoncapaResponse):
    '''
    TODO: handle direction and randomize
    '''

    response_tag = 'optionresponse'
    hint_tag = 'optionhint'
    allowed_inputfields = ['optioninput']

    def setup_response(self):
        self.answer_fields = self.inputfields

    def get_score(self, student_answers):
        # log.debug('%s: student_answers=%s' % (unicode(self),student_answers))
        cmap = CorrectMap()
        amap = self.get_answers()
        for aid in amap:
            if aid in student_answers and student_answers[aid] == amap[aid]:
                cmap.set(aid, 'correct')
            else:
                cmap.set(aid, 'incorrect')
        return cmap

    def get_answers(self):
        amap = dict([(af.get('id'), contextualize_text(af.get(
            'correct'), self.context)) for af in self.answer_fields])
        # log.debug('%s: expected answers=%s' % (unicode(self),amap))
        return amap

#-----------------------------------------------------------------------------


class NumericalResponse(LoncapaResponse):
    '''
    This response type expects a number or formulaic expression that evaluates
    to a number (e.g. `4+5/2^2`), and accepts with a tolerance.
    '''

    response_tag = 'numericalresponse'
    hint_tag = 'numericalhint'
    allowed_inputfields = ['textline', 'formulaequationinput']
    required_attributes = ['answer']
    max_inputfields = 1

    def setup_response(self):
        xml = self.xml
        context = self.context
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        try:
            self.tolerance_xml = xml.xpath(
                '//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except IndexError:  # xpath found an empty list, so (...)[0] is the error
            self.tolerance = '0'

    def get_score(self, student_answers):
        '''Grade a numeric response '''
        student_answer = student_answers[self.answer_id]

        try:
            correct_ans = complex(self.correct_answer)
        except ValueError:
            log.debug("Content error--answer '{0}' is not a valid complex number".format(
                self.correct_answer))
            raise StudentInputError(
                "There was a problem with the staff answer to this problem")

        try:
            correct = compare_with_tolerance(
                evaluator(dict(), dict(), student_answer),
                correct_ans, self.tolerance)
        # We should catch this explicitly.
        # I think this is just pyparsing.ParseException, calc.UndefinedVariable:
        # But we'd need to confirm
        except:
            # Use the traceback-preserving version of re-raising with a
            # different type
            type, value, traceback = sys.exc_info()

            raise StudentInputError, ("Could not interpret '%s' as a number" %
                                      cgi.escape(student_answer)), traceback

        if correct:
            return CorrectMap(self.answer_id, 'correct')
        else:
            return CorrectMap(self.answer_id, 'incorrect')

    # TODO: add check_hint_condition(self, hxml_set, student_answers)

    def get_answers(self):
        return {self.answer_id: self.correct_answer}

#-----------------------------------------------------------------------------


class StringResponse(LoncapaResponse):

    response_tag = 'stringresponse'
    hint_tag = 'stringhint'
    allowed_inputfields = ['textline']
    required_attributes = ['answer']
    max_inputfields = 1

    def setup_response(self):
        self.correct_answer = contextualize_text(
            self.xml.get('answer'), self.context).strip()

    def get_score(self, student_answers):
        '''Grade a string response '''
        student_answer = student_answers[self.answer_id].strip()
        correct = self.check_string(self.correct_answer, student_answer)
        return CorrectMap(self.answer_id, 'correct' if correct else 'incorrect')

    def check_string(self, expected, given):
        if self.xml.get('type') == 'ci':
            return given.lower() == expected.lower()
        return given == expected

    def check_hint_condition(self, hxml_set, student_answers):
        given = student_answers[self.answer_id].strip()
        hints_to_show = []
        for hxml in hxml_set:
            name = hxml.get('name')
            correct_answer = contextualize_text(
                hxml.get('answer'), self.context).strip()
            if self.check_string(correct_answer, given):
                hints_to_show.append(name)
        log.debug('hints_to_show = %s' % hints_to_show)
        return hints_to_show

    def get_answers(self):
        return {self.answer_id: self.correct_answer}

#-----------------------------------------------------------------------------


class CustomResponse(LoncapaResponse):
    '''
    Custom response.  The python code to be run should be in <answer>...</answer>
    or in a <script>...</script>
    '''

    response_tag = 'customresponse'

    allowed_inputfields = ['textline', 'textbox', 'crystallography',
                           'chemicalequationinput', 'vsepr_input',
                           'drag_and_drop_input', 'editamoleculeinput',
                           'designprotein2dinput', 'editageneinput',
                           'annotationinput', 'jsinput', 'formulaequationinput']

    def setup_response(self):
        xml = self.xml

        # if <customresponse> has an "expect" (or "answer") attribute then save
        # that
        self.expect = xml.get('expect') or xml.get('answer')

        log.debug('answer_ids=%s' % self.answer_ids)

        # the <answer>...</answer> stanza should be local to the current <customresponse>.
        # So try looking there first.
        self.code = None
        answer = None
        try:
            answer = xml.xpath('//*[@id=$id]//answer', id=xml.get('id'))[0]
        except IndexError:
            # print "xml = ",etree.tostring(xml,pretty_print=True)

            # if we have a "cfn" attribute then look for the function specified by cfn, in
            # the problem context ie the comparison function is defined in the
            # <script>...</script> stanza instead
            cfn = xml.get('cfn')
            if cfn:
                log.debug("cfn = %s" % cfn)

                # This is a bit twisty.  We used to grab the cfn function from
                # the context, but now that we sandbox Python execution, we
                # can't get functions from previous executions.  So we make an
                # actual function that will re-execute the original script,
                # and invoke the function with the data needed.
                def make_check_function(script_code, cfn):
                    def check_function(expect, ans, **kwargs):
                        extra_args = "".join(", {0}={0}".format(k) for k in kwargs)
                        code = (
                            script_code + "\n" +
                            "cfn_return = %s(expect, ans%s)\n" % (cfn, extra_args)
                        )
                        globals_dict = {
                            'expect': expect,
                            'ans': ans,
                        }
                        globals_dict.update(kwargs)
                        safe_exec.safe_exec(
                            code,
                            globals_dict,
                            python_path=self.context['python_path'],
                            slug=self.id,
                            random_seed=self.context['seed'],
                            unsafely=self.system.can_execute_unsafe_code(),
                        )
                        return globals_dict['cfn_return']
                    return check_function

                self.code = make_check_function(self.context['script_code'], cfn)

        if not self.code:
            if answer is None:
                log.error("[courseware.capa.responsetypes.customresponse] missing"
                          " code checking script! id=%s" % self.id)
                self.code = ''
            else:
                answer_src = answer.get('src')
                if answer_src is not None:
                    self.code = self.system.filesystem.open(
                        'src/' + answer_src).read()
                else:
                    self.code = answer.text

    def get_score(self, student_answers):
        '''
        student_answers is a dict with everything from request.POST, but with the first part
        of each key removed (the string before the first "_").
        '''

        log.debug('%s: student_answers=%s' % (unicode(self), student_answers))

        # ordered list of answer id's
        idset = sorted(self.answer_ids)
        try:
            # ordered list of answers
            submission = [student_answers[k] for k in idset]
        except Exception as err:
            msg = ('[courseware.capa.responsetypes.customresponse] error getting'
                   ' student answer from %s' % student_answers)
            msg += '\n idset = %s, error = %s' % (idset, err)
            log.error(msg)
            raise Exception(msg)

        # global variable in context which holds the Presentation MathML from dynamic math input
        # ordered list of dynamath responses
        dynamath = [student_answers.get(k + '_dynamath', None) for k in idset]

        # if there is only one box, and it's empty, then don't evaluate
        if len(idset) == 1 and not submission[0]:
            # default to no error message on empty answer (to be consistent with other
            # responsetypes) but allow author to still have the old behavior by setting
            # empty_answer_err attribute
            msg = ('<span class="inline-error">No answer entered!</span>'
                   if self.xml.get('empty_answer_err') else '')
            return CorrectMap(idset[0], 'incorrect', msg=msg)

        # NOTE: correct = 'unknown' could be dangerous. Inputtypes such as textline are
        # not expecting 'unknown's
        correct = ['unknown'] * len(idset)
        messages = [''] * len(idset)
        overall_message = ""

        # put these in the context of the check function evaluator
        # note that this doesn't help the "cfn" version - only the exec version
        self.context.update({
            # my ID
            'response_id': self.id,

            # expected answer (if given as attribute)
            'expect': self.expect,

            # ordered list of student answers from entry boxes in our subtree
            'submission': submission,

            # ordered list of ID's of all entry boxes in our subtree
            'idset': idset,

            # ordered list of all javascript inputs in our subtree
            'dynamath': dynamath,

            # dict of student's responses, with keys being entry box IDs
            'answers': student_answers,

            # the list to be filled in by the check function
            'correct': correct,

            # the list of messages to be filled in by the check function
            'messages': messages,

            # a message that applies to the entire response
            # instead of a particular input
            'overall_message': overall_message,

            # any options to be passed to the cfn
            'options': self.xml.get('options'),
            'testdat': 'hello world',
        })

        # pass self.system.debug to cfn
        self.context['debug'] = self.system.DEBUG

        # Run the check function
        self.execute_check_function(idset, submission)

        # build map giving "correct"ness of the answer(s)
        correct = self.context['correct']
        messages = self.context['messages']
        overall_message = self.clean_message_html(self.context['overall_message'])
        correct_map = CorrectMap()
        correct_map.set_overall_message(overall_message)

        for k in range(len(idset)):
            npoints = self.maxpoints[idset[k]] if correct[k] == 'correct' else 0
            correct_map.set(idset[k], correct[k], msg=messages[k],
                            npoints=npoints)
        return correct_map

    def execute_check_function(self, idset, submission):
        # exec the check function
        if isinstance(self.code, basestring):
            try:
                safe_exec.safe_exec(
                    self.code,
                    self.context,
                    cache=self.system.cache,
                    slug=self.id,
                    random_seed=self.context['seed'],
                    unsafely=self.system.can_execute_unsafe_code(),
                )
            except Exception as err:
                self._handle_exec_exception(err)

        else:
            # self.code is not a string; it's a function we created earlier.

            # this is an interface to the Tutor2 check functions
            fn = self.code
            answer_given = submission[0] if (len(idset) == 1) else submission
            kwnames = self.xml.get("cfn_extra_args", "").split()
            kwargs = {n:self.context.get(n) for n in kwnames}
            log.debug(" submission = %s" % submission)
            try:
                ret = fn(self.expect, answer_given, **kwargs)
            except Exception as err:
                self._handle_exec_exception(err)
            log.debug(
                "[courseware.capa.responsetypes.customresponse.get_score] ret = %s",
                ret
            )
            if isinstance(ret, dict):
                # One kind of dictionary the check function can return has the
                # form {'ok': BOOLEAN, 'msg': STRING}
                # If there are multiple inputs, they all get marked
                # to the same correct/incorrect value
                if 'ok' in ret:
                    correct = ['correct' if ret['ok'] else 'incorrect'] * len(idset)
                    msg = ret.get('msg', None)
                    msg = self.clean_message_html(msg)

                    # If there is only one input, apply the message to that input
                    # Otherwise, apply the message to the whole problem
                    if len(idset) > 1:
                        self.context['overall_message'] = msg
                    else:
                        self.context['messages'][0] = msg

                # Another kind of dictionary the check function can return has
                # the form:
                # {'overall_message': STRING,
                #  'input_list': [{ 'ok': BOOLEAN, 'msg': STRING }, ...] }
                #
                # This allows the function to return an 'overall message'
                # that applies to the entire problem, as well as correct/incorrect
                # status and messages for individual inputs
                elif 'input_list' in ret:
                    overall_message = ret.get('overall_message', '')
                    input_list = ret['input_list']

                    correct = []
                    messages = []
                    for input_dict in input_list:
                        correct.append('correct'
                                       if input_dict['ok'] else 'incorrect')
                        msg = (self.clean_message_html(input_dict['msg'])
                               if 'msg' in input_dict else None)
                        messages.append(msg)
                    self.context['messages'] = messages
                    self.context['overall_message'] = overall_message

                # Otherwise, we do not recognize the dictionary
                # Raise an exception
                else:
                    log.error(traceback.format_exc())
                    raise ResponseError(
                        "CustomResponse: check function returned an invalid dict")

            else:
                correct = ['correct' if ret else 'incorrect'] * len(idset)

            self.context['correct'] = correct

    def clean_message_html(self, msg):

        # If *msg* is an empty string, then the code below
        # will return "</html>".  To avoid this, we first check
        # that *msg* is a non-empty string.
        if msg:

            # When we parse *msg* using etree, there needs to be a root
            # element, so we wrap the *msg* text in <html> tags
            msg = '<html>' + msg + '</html>'

            # Replace < characters
            msg = msg.replace('&#60;', '&lt;')

            # Use etree to prettify the HTML
            msg = etree.tostring(fromstring_bs(msg, convertEntities=None),
                                 pretty_print=True)

            msg = msg.replace('&#13;', '')

            # Remove the <html> tags we introduced earlier, so we're
            # left with just the prettified message markup
            msg = re.sub('(?ms)<html>(.*)</html>', '\\1', msg)

            # Strip leading and trailing whitespace
            return msg.strip()

        # If we start with an empty string, then return an empty string
        else:
            return ""

    def get_answers(self):
        '''
        Give correct answer expected for this response.

        use default_answer_map from entry elements (eg textline),
        when this response has multiple entry objects.

        but for simplicity, if an "expect" attribute was given by the content author
        ie <customresponse expect="foo" ...> then that.
        '''
        if len(self.answer_ids) > 1:
            return self.default_answer_map
        if self.expect:
            return {self.answer_ids[0]: self.expect}
        return self.default_answer_map

    def _handle_exec_exception(self, err):
        '''
        Handle an exception raised during the execution of
        custom Python code.

        Raises a ResponseError
        '''

        # Log the error if we are debugging
        msg = 'Error occurred while evaluating CustomResponse'
        log.warning(msg, exc_info=True)

        # Notify student with a student input error
        _, _, traceback_obj = sys.exc_info()
        raise ResponseError, err.message, traceback_obj

#-----------------------------------------------------------------------------


class SymbolicResponse(CustomResponse):
    """
    Symbolic math response checking, using symmath library.
    """

    response_tag = 'symbolicresponse'
    max_inputfields = 1

    def setup_response(self):
        # Symbolic response always uses symmath_check()
        # If the XML did not specify this, then set it now
        # Otherwise, we get an error from the superclass
        self.xml.set('cfn', 'symmath_check')

        # Let CustomResponse do its setup
        super(SymbolicResponse, self).setup_response()

    def execute_check_function(self, idset, submission):
        from symmath import symmath_check
        try:
            # Since we have limited max_inputfields to 1,
            # we can assume that there is only one submission
            answer_given = submission[0]

            ret = symmath_check(
                self.expect, answer_given,
                dynamath=self.context.get('dynamath'),
                options=self.context.get('options'),
                debug=self.context.get('debug'),
            )
        except Exception as err:
            log.error("oops in symbolicresponse (cfn) error %s" % err)
            log.error(traceback.format_exc())
            raise Exception("oops in symbolicresponse (cfn) error %s" % err)
        self.context['messages'][0] = self.clean_message_html(ret['msg'])
        self.context['correct'] = ['correct' if ret['ok'] else 'incorrect'] * len(idset)

#-----------------------------------------------------------------------------

"""
valid:       Flag indicating valid score_msg format (Boolean)
correct:     Correctness of submission (Boolean)
score:       Points to be assigned (numeric, can be float)
msg:         Message from grader to display to student (string)
"""
ScoreMessage = namedtuple('ScoreMessage',
                          ['valid', 'correct', 'points', 'msg'])


class CodeResponse(LoncapaResponse):
    """
    Grade student code using an external queueing server, called 'xqueue'

    Expects 'xqueue' dict in ModuleSystem with the following keys that are needed by CodeResponse:
        system.xqueue = { 'interface': XqueueInterface object,
                          'construct_callback': Per-StudentModule callback URL
                                          constructor, defaults to using 'score_update'
                                          as the correct dispatch (function),
                          'default_queuename': Default queuename to submit request (string)
                        }

    External requests are only submitted for student submission grading
        (i.e. and not for getting reference answers)
    """

    response_tag = 'coderesponse'
    allowed_inputfields = ['textbox', 'filesubmission', 'matlabinput']
    max_inputfields = 1

    def setup_response(self):
        '''
        Configure CodeResponse from XML. Supports both CodeResponse and ExternalResponse XML

        TODO: Determines whether in synchronous or asynchronous (queued) mode
        '''
        xml = self.xml
        # TODO: XML can override external resource (grader/queue) URL
        self.url = xml.get('url', None)

        # We do not support xqueue within Studio.
        if self.system.xqueue is not None:
            default_queuename = self.system.xqueue['default_queuename']
        else:
            default_queuename = None
        self.queue_name = xml.get('queuename', default_queuename)

        # VS[compat]:
        # Check if XML uses the ExternalResponse format or the generic
        # CodeResponse format
        codeparam = self.xml.find('codeparam')
        assert codeparam is not None, "Unsupported old format! <coderesponse> without <codeparam>"
        self._parse_coderesponse_xml(codeparam)

    def _parse_coderesponse_xml(self, codeparam):
        '''
        Parse the new CodeResponse XML format. When successful, sets:
            self.initial_display
            self.answer (an answer to display to the student in the LMS)
            self.payload
        '''
        # Note that CodeResponse is agnostic to the specific contents of
        # grader_payload
        grader_payload = codeparam.find('grader_payload')
        grader_payload = grader_payload.text if grader_payload is not None else ''
        self.payload = {'grader_payload': grader_payload}

        self.initial_display = find_with_default(
            codeparam, 'initial_display', '')
        self.answer = find_with_default(codeparam, 'answer_display',
                                        'No answer provided.')

    def get_score(self, student_answers):
        try:
            # Note that submission can be a file
            submission = student_answers[self.answer_id]
        except Exception as err:
            log.error(
                'Error in CodeResponse %s: cannot get student answer for %s;'
                ' student_answers=%s' %
                (err, self.answer_id, convert_files_to_filenames(student_answers))
            )
            raise Exception(err)

        # We do not support xqueue within Studio.
        if self.system.xqueue is None:
            cmap = CorrectMap()
            cmap.set(self.answer_id, queuestate=None,
                     msg='Error checking problem: no external queueing server is configured.')
            return cmap

        # Prepare xqueue request
        #------------------------------------------------------------

        qinterface = self.system.xqueue['interface']
        qtime = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)

        anonymous_student_id = self.system.anonymous_student_id

        # Generate header
        queuekey = xqueue_interface.make_hashkey(
            str(self.system.seed) + qtime + anonymous_student_id + self.answer_id
        )
        callback_url = self.system.xqueue['construct_callback']()
        xheader = xqueue_interface.make_xheader(
            lms_callback_url=callback_url,
            lms_key=queuekey,
            queue_name=self.queue_name
        )

        # Generate body
        if is_list_of_files(submission):
            # TODO: Get S3 pointer from the Queue
            self.context.update({'submission': ''})
        else:
            self.context.update({'submission': submission})

        contents = self.payload.copy()

        # Metadata related to the student submission revealed to the external
        # grader
        student_info = {
            'anonymous_student_id': anonymous_student_id,
            'submission_time': qtime,
        }
        contents.update({'student_info': json.dumps(student_info)})

        # Submit request. When successful, 'msg' is the prior length of the
        # queue

        if is_list_of_files(submission):
            # TODO: Is there any information we want to send here?
            contents.update({'student_response': ''})
            (error, msg) = qinterface.send_to_queue(header=xheader,
                                                    body=json.dumps(contents),
                                                    files_to_upload=submission)
        else:
            contents.update({'student_response': submission})
            (error, msg) = qinterface.send_to_queue(header=xheader,
                                                    body=json.dumps(contents))

        # State associated with the queueing request
        queuestate = {'key': queuekey,
                      'time': qtime, }

        cmap = CorrectMap()
        if error:
            cmap.set(self.answer_id, queuestate=None,
                     msg='Unable to deliver your submission to grader. (Reason: %s.)'
                         ' Please try again later.' % msg)
        else:
            # Queueing mechanism flags:
            #   1) Backend: Non-null CorrectMap['queuestate'] indicates that
            #      the problem has been queued
            #   2) Frontend: correctness='incomplete' eventually trickles down
            #      through inputtypes.textbox and .filesubmission to inform the
            #      browser to poll the LMS
            cmap.set(self.answer_id, queuestate=queuestate,
                     correctness='incomplete', msg=msg)

        return cmap

    def update_score(self, score_msg, oldcmap, queuekey):

        (valid_score_msg, correct, points,
         msg) = self._parse_score_msg(score_msg)
        if not valid_score_msg:
            oldcmap.set(self.answer_id,
                        msg='Invalid grader reply. Please contact the course staff.')
            return oldcmap

        correctness = 'correct' if correct else 'incorrect'

        # TODO: Find out how this is used elsewhere, if any
        self.context['correct'] = correctness

        # Replace 'oldcmap' with new grading results if queuekey matches.  If queuekey
        # does not match, we keep waiting for the score_msg whose key actually
        # matches
        if oldcmap.is_right_queuekey(self.answer_id, queuekey):
            # Sanity check on returned points
            if points < 0:
                points = 0
            # Queuestate is consumed
            oldcmap.set(
                self.answer_id, npoints=points, correctness=correctness,
                msg=msg.replace('&nbsp;', '&#160;'), queuestate=None)
        else:
            log.debug('CodeResponse: queuekey %s does not match for answer_id=%s.' %
                      (queuekey, self.answer_id))

        return oldcmap

    def get_answers(self):
        anshtml = '<span class="code-answer"><pre><code>%s</code></pre></span>' % self.answer
        return {self.answer_id: anshtml}

    def get_initial_display(self):
        return {self.answer_id: self.initial_display}

    def _parse_score_msg(self, score_msg):
        """
         Grader reply is a JSON-dump of the following dict
           { 'correct': True/False,
             'score': Numeric value (floating point is okay) to assign to answer
             'msg': grader_msg }

        Returns (valid_score_msg, correct, score, msg):
            valid_score_msg: Flag indicating valid score_msg format (Boolean)
            correct:         Correctness of submission (Boolean)
            score:           Points to be assigned (numeric, can be float)
            msg:             Message from grader to display to student (string)
        """
        fail = (False, False, 0, '')
        try:
            score_result = json.loads(score_msg)
        except (TypeError, ValueError):
            log.error("External grader message should be a JSON-serialized dict."
                      " Received score_msg = %s" % score_msg)
            return fail
        if not isinstance(score_result, dict):
            log.error("External grader message should be a JSON-serialized dict."
                      " Received score_result = %s" % score_result)
            return fail
        for tag in ['correct', 'score', 'msg']:
            if tag not in score_result:
                log.error("External grader message is missing one or more required"
                          " tags: 'correct', 'score', 'msg'")
                return fail

        # Next, we need to check that the contents of the external grader message
        #   is safe for the LMS.
        # 1) Make sure that the message is valid XML (proper opening/closing tags)
        # 2) TODO: Is the message actually HTML?
        msg = score_result['msg']
        try:
            etree.fromstring(msg)
        except etree.XMLSyntaxError as err:
            log.error("Unable to parse external grader message as valid"
                      " XML: score_msg['msg']=%s" % msg)
            return fail

        return (True, score_result['correct'], score_result['score'], msg)


#-----------------------------------------------------------------------------


class ExternalResponse(LoncapaResponse):
    '''
    Grade the students input using an external server.

    Typically used by coding problems.

    '''

    response_tag = 'externalresponse'
    allowed_inputfields = ['textline', 'textbox']

    def setup_response(self):
        xml = self.xml
        # FIXME - hardcoded URL
        self.url = xml.get('url') or "http://qisx.mit.edu:8889/pyloncapa"

        answer = xml.find('answer')
        if answer is not None:
            answer_src = answer.get('src')
            if answer_src is not None:
                self.code = self.system.filesystem.open(
                    'src/' + answer_src).read()
            else:
                self.code = answer.text
        else:
            # no <answer> stanza; get code from <script>
            self.code = self.context['script_code']
            if not self.code:
                msg = '%s: Missing answer script code for externalresponse' % unicode(
                    self)
                msg += "\nSee XML source line %s" % getattr(
                    self.xml, 'sourceline', '<unavailable>')
                raise LoncapaProblemError(msg)

        self.tests = xml.get('tests')

    def do_external_request(self, cmd, extra_payload):
        '''
        Perform HTTP request / post to external server.

        cmd = remote command to perform (str)
        extra_payload = dict of extra stuff to post.

        Return XML tree of response (from response body)
        '''
        xmlstr = etree.tostring(self.xml, pretty_print=True)
        payload = {'xml': xmlstr,
                   'edX_cmd': cmd,
                   'edX_tests': self.tests,
                   'processor': self.code,
                   }
        payload.update(extra_payload)

        try:
            # call external server. TODO: synchronous call, can block for a
            # long time
            r = requests.post(self.url, data=payload)
        except Exception as err:
            msg = 'Error %s - cannot connect to external server url=%s' % (
                err, self.url)
            log.error(msg)
            raise Exception(msg)

        if self.system.DEBUG:
            log.info('response = %s' % r.text)

        if (not r.text) or (not r.text.strip()):
            raise Exception(
                'Error: no response from external server url=%s' % self.url)

        try:
            # response is XML; parse it
            rxml = etree.fromstring(r.text)
        except Exception as err:
            msg = 'Error %s - cannot parse response from external server r.text=%s' % (
                err, r.text)
            log.error(msg)
            raise Exception(msg)

        return rxml

    def get_score(self, student_answers):
        idset = sorted(self.answer_ids)
        cmap = CorrectMap()
        try:
            submission = [student_answers[k] for k in idset]
        except Exception as err:
            log.error('Error %s: cannot get student answer for %s; student_answers=%s' %
                      (err, self.answer_ids, student_answers))
            raise Exception(err)

        self.context.update({'submission': submission})

        extra_payload = {'edX_student_response': json.dumps(submission)}

        try:
            rxml = self.do_external_request('get_score', extra_payload)
        except Exception as err:
            log.error('Error %s' % err)
            if self.system.DEBUG:
                cmap.set_dict(dict(zip(sorted(
                    self.answer_ids), ['incorrect'] * len(idset))))
                cmap.set_property(
                    self.answer_ids[0], 'msg',
                    '<span class="inline-error">%s</span>' % str(err).replace('<', '&lt;'))
                return cmap

        ad = rxml.find('awarddetail').text
        admap = {'EXACT_ANS': 'correct',         # TODO: handle other loncapa responses
                 'WRONG_FORMAT': 'incorrect',
                 }
        self.context['correct'] = ['correct']
        if ad in admap:
            self.context['correct'][0] = admap[ad]

        # create CorrectMap
        for key in idset:
            idx = idset.index(key)
            msg = rxml.find('message').text.replace(
                '&nbsp;', '&#160;') if idx == 0 else None
            cmap.set(key, self.context['correct'][idx], msg=msg)

        return cmap

    def get_answers(self):
        '''
        Use external server to get expected answers
        '''
        try:
            rxml = self.do_external_request('get_answers', {})
            exans = json.loads(rxml.find('expected').text)
        except Exception as err:
            log.error('Error %s' % err)
            if self.system.DEBUG:
                msg = '<span class="inline-error">%s</span>' % str(
                    err).replace('<', '&lt;')
                exans = [''] * len(self.answer_ids)
                exans[0] = msg

        if not (len(exans) == len(self.answer_ids)):
            log.error('Expected %d answers from external server, only got %d!' %
                      (len(self.answer_ids), len(exans)))
            raise Exception('Short response from external server')
        return dict(zip(self.answer_ids, exans))


#-----------------------------------------------------------------------------

class FormulaResponse(LoncapaResponse):
    '''
    Checking of symbolic math response using numerical sampling.
    '''

    response_tag = 'formularesponse'
    hint_tag = 'formulahint'
    allowed_inputfields = ['textline', 'formulaequationinput']
    required_attributes = ['answer', 'samples']
    max_inputfields = 1

    def setup_response(self):
        xml = self.xml
        context = self.context
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.samples = contextualize_text(xml.get('samples'), context)
        try:
            self.tolerance_xml = xml.xpath(
                '//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except Exception:
            self.tolerance = '0.00001'

        ts = xml.get('type')
        if ts is None:
            typeslist = []
        else:
            typeslist = ts.split(',')
        if 'ci' in typeslist:
            # Case insensitive
            self.case_sensitive = False
        elif 'cs' in typeslist:
            # Case sensitive
            self.case_sensitive = True
        else:
            # Default
            self.case_sensitive = False

    def get_score(self, student_answers):
        given = student_answers[self.answer_id]
        correctness = self.check_formula(
            self.correct_answer, given, self.samples)
        return CorrectMap(self.answer_id, correctness)

    def check_formula(self, expected, given, samples):
        variables = samples.split('@')[0].split(',')
        numsamples = int(samples.split('@')[1].split('#')[1])
        sranges = zip(*map(lambda x: map(float, x.split(",")),
                           samples.split('@')[1].split('#')[0].split(':')))

        ranges = dict(zip(variables, sranges))
        for _ in range(numsamples):
            instructor_variables = self.strip_dict(dict(self.context))
            student_variables = dict()
            # ranges give numerical ranges for testing
            for var in ranges:
                # TODO: allow specified ranges (i.e. integers and complex numbers) for random variables
                value = random.uniform(*ranges[var])
                instructor_variables[str(var)] = value
                student_variables[str(var)] = value
            # log.debug('formula: instructor_vars=%s, expected=%s' %
            # (instructor_variables,expected))

            # Call `evaluator` on the instructor's answer and get a number
            instructor_result = evaluator(
                instructor_variables, dict(),
                expected, case_sensitive=self.case_sensitive
            )
            try:
                # log.debug('formula: student_vars=%s, given=%s' %
                # (student_variables,given))

                # Call `evaluator` on the student's answer; look for exceptions
                student_result = evaluator(
                    student_variables,
                    dict(),
                    given,
                    case_sensitive=self.case_sensitive
                )
            except UndefinedVariable as uv:
                log.debug(
                    'formularesponse: undefined variable in given=%s',
                    given
                )
                raise StudentInputError(
                    "Invalid input: " + uv.message + " not permitted in answer"
                )
            except ValueError as ve:
                if 'factorial' in ve.message:
                    # This is thrown when fact() or factorial() is used in a formularesponse answer
                    #   that tests on negative and/or non-integer inputs
                    # ve.message will be: `factorial() only accepts integral values` or
                    # `factorial() not defined for negative values`
                    log.debug(
                        ('formularesponse: factorial function used in response '
                         'that tests negative and/or non-integer inputs. '
                         'given={0}').format(given)
                    )
                    raise StudentInputError(
                        ("factorial function not permitted in answer "
                         "for this problem. Provided answer was: "
                         "{0}").format(cgi.escape(given))
                    )
                # If non-factorial related ValueError thrown, handle it the same as any other Exception
                log.debug('formularesponse: error {0} in formula'.format(ve))
                raise StudentInputError("Invalid input: Could not parse '%s' as a formula" %
                                        cgi.escape(given))
            except Exception as err:
                # traceback.print_exc()
                log.debug('formularesponse: error %s in formula', err)
                raise StudentInputError("Invalid input: Could not parse '%s' as a formula" %
                                        cgi.escape(given))

            # No errors in student's response--actually test for correctness
            if not compare_with_tolerance(student_result, instructor_result, self.tolerance):
                return "incorrect"
        return "correct"

    def strip_dict(self, d):
        ''' Takes a dict. Returns an identical dict, with all non-word
        keys and all non-numeric values stripped out. All values also
        converted to float. Used so we can safely use Python contexts.
        '''
        d = dict([(k, numpy.complex(d[k])) for k in d if type(k) == str and
                  k.isalnum() and
                  isinstance(d[k], numbers.Number)])
        return d

    def check_hint_condition(self, hxml_set, student_answers):
        given = student_answers[self.answer_id]
        hints_to_show = []
        for hxml in hxml_set:
            samples = hxml.get('samples')
            name = hxml.get('name')
            correct_answer = contextualize_text(
                hxml.get('answer'), self.context)
            try:
                correctness = self.check_formula(
                    correct_answer, given, samples)
            except Exception:
                correctness = 'incorrect'
            if correctness == 'correct':
                hints_to_show.append(name)
        log.debug('hints_to_show = %s' % hints_to_show)
        return hints_to_show

    def get_answers(self):
        return {self.answer_id: self.correct_answer}

#-----------------------------------------------------------------------------


class SchematicResponse(LoncapaResponse):

    response_tag = 'schematicresponse'
    allowed_inputfields = ['schematic']

    def setup_response(self):
        xml = self.xml
        answer = xml.xpath('//*[@id=$id]//answer', id=xml.get('id'))[0]
        answer_src = answer.get('src')
        if answer_src is not None:
            # Untested; never used
            self.code = self.system.filestore.open('src/' + answer_src).read()
        else:
            self.code = answer.text

    def get_score(self, student_answers):
        #from capa_problem import global_context
        submission = [
            json.loads(student_answers[k]) for k in sorted(self.answer_ids)
        ]
        self.context.update({'submission': submission})
        try:
            safe_exec.safe_exec(
                self.code,
                self.context,
                cache=self.system.cache,
                slug=self.id,
                random_seed=self.context['seed'],
                unsafely=self.system.can_execute_unsafe_code(),
            )
        except Exception as err:
            msg = 'Error %s in evaluating SchematicResponse' % err
            raise ResponseError(msg)
        cmap = CorrectMap()
        cmap.set_dict(dict(zip(sorted(self.answer_ids), self.context['correct'])))
        return cmap

    def get_answers(self):
        # use answers provided in input elements
        return self.default_answer_map

#-----------------------------------------------------------------------------


class ImageResponse(LoncapaResponse):
    """
    Handle student response for image input: the input is a click on an image,
    which produces an [x,y] coordinate pair.  The click is correct if it falls
    within a region specified.  This region is a union of rectangles.

    Lon-CAPA requires that each <imageresponse> has a <foilgroup> inside it.
    That doesn't make sense to me (Ike).  Instead, let's have it such that
    <imageresponse> should contain one or more <imageinput> stanzas.
    Each <imageinput> should specify a rectangle(s) or region(s), given as an
    attribute, defining the correct answer.

    <imageinput src="/static/images/Lecture2/S2_p04.png" width="811" height="610"
    rectangle="(10,10)-(20,30);(12,12)-(40,60)"
    regions="[[[10,10], [20,30], [40, 10]], [[100,100], [120,130], [110,150]]]"/>

    Regions is list of lists [region1, region2, region3, ...] where regionN
    is disordered list of points: [[1,1], [100,100], [50,50], [20, 70]].

    If there is only one region in the list, simpler notation can be used:
    regions="[[10,10], [30,30], [10, 30], [30, 10]]" (without explicitly
        setting outer list)

    Returns:
        True, if click is inside any region or rectangle. Otherwise False.
    """

    response_tag = 'imageresponse'
    allowed_inputfields = ['imageinput']

    def setup_response(self):
        self.ielements = self.inputfields
        self.answer_ids = [ie.get('id') for ie in self.ielements]

    def get_score(self, student_answers):
        correct_map = CorrectMap()
        expectedset = self.get_mapped_answers()
        for aid in self.answer_ids:  # loop through IDs of <imageinput>
        #  fields in our stanza
            given = student_answers[
                aid]  # this should be a string of the form '[x,y]'
            correct_map.set(aid, 'incorrect')
            if not given:  # No answer to parse. Mark as incorrect and move on
                continue
            # parse given answer
            m = re.match(r'\[([0-9]+),([0-9]+)]', given.strip().replace(' ', ''))
            if not m:
                raise Exception('[capamodule.capa.responsetypes.imageinput] '
                                'error grading %s (input=%s)' % (aid, given))
            (gx, gy) = [int(x) for x in m.groups()]

            rectangles, regions = expectedset
            if rectangles[aid]:  # rectangles part - for backward compatibility
                # Check whether given point lies in any of the solution
                # rectangles
                solution_rectangles = rectangles[aid].split(';')
                for solution_rectangle in solution_rectangles:
                    # parse expected answer
                    # TODO: Compile regexp on file load
                    m = re.match(
                        r'[\(\[]([0-9]+),([0-9]+)[\)\]]-[\(\[]([0-9]+),([0-9]+)[\)\]]',
                        solution_rectangle.strip().replace(' ', ''))
                    if not m:
                        msg = 'Error in problem specification! cannot parse rectangle in %s' % (
                            etree.tostring(self.ielements[aid], pretty_print=True))
                        raise Exception(
                            '[capamodule.capa.responsetypes.imageinput] ' + msg)
                    (llx, lly, urx, ury) = [int(x) for x in m.groups()]

                    # answer is correct if (x,y) is within the specified
                    # rectangle
                    if (llx <= gx <= urx) and (lly <= gy <= ury):
                        correct_map.set(aid, 'correct')
                        break
            if correct_map[aid]['correctness'] != 'correct' and regions[aid]:
                parsed_region = json.loads(regions[aid])
                if parsed_region:
                    if type(parsed_region[0][0]) != list:
                        # we have [[1,2],[3,4],[5,6]] - single region
                        # instead of [[[1,2],[3,4],[5,6], [[1,2],[3,4],[5,6]]]
                        # or [[[1,2],[3,4],[5,6]]] - multiple regions syntax
                        parsed_region = [parsed_region]
                    for region in parsed_region:
                        polygon = MultiPoint(region).convex_hull
                        if (polygon.type == 'Polygon' and
                                polygon.contains(Point(gx, gy))):
                            correct_map.set(aid, 'correct')
                            break
        return correct_map

    def get_mapped_answers(self):
        '''
        Returns the internal representation of the answers

        Input:
            None
        Returns:
            tuple (dict, dict) -
                rectangles (dict) - a map of inputs to the defined rectangle for that input
                regions (dict) - a map of inputs to the defined region for that input
        '''
        answers = (
            dict([(ie.get('id'), ie.get(
                'rectangle')) for ie in self.ielements]),
            dict([(ie.get('id'), ie.get('regions')) for ie in self.ielements]))
        return answers

    def get_answers(self):
        '''
        Returns the external representation of the answers

        Input:
            None
        Returns:
            dict (str, (str, str)) - a map of inputs to a tuple of their rectange
                and their regions
        '''
        answers = {}
        for ie in self.ielements:
            ie_id = ie.get('id')
            answers[ie_id] = (ie.get('rectangle'), ie.get('regions'))

        return answers

#-----------------------------------------------------------------------------


class AnnotationResponse(LoncapaResponse):
    '''
    Checking of annotation responses.

    The response contains both a comment (student commentary) and an option (student tag).
    Only the tag is currently graded. Answers may be incorrect, partially correct, or correct.
    '''
    response_tag = 'annotationresponse'
    allowed_inputfields = ['annotationinput']
    max_inputfields = 1
    default_scoring = {'incorrect': 0, 'partially-correct': 1, 'correct': 2}

    def setup_response(self):
        xml = self.xml
        self.scoring_map = self._get_scoring_map()
        self.answer_map = self._get_answer_map()
        self.maxpoints = self._get_max_points()

    def get_score(self, student_answers):
        ''' Returns a CorrectMap for the student answer, which may include
            partially correct answers.'''
        student_answer = student_answers[self.answer_id]
        student_option = self._get_submitted_option_id(student_answer)

        scoring = self.scoring_map[self.answer_id]
        is_valid = student_option is not None and student_option in scoring.keys(
        )

        (correctness, points) = ('incorrect', None)
        if is_valid:
            correctness = scoring[student_option]['correctness']
            points = scoring[student_option]['points']

        return CorrectMap(self.answer_id, correctness=correctness, npoints=points)

    def get_answers(self):
        return self.answer_map

    def _get_scoring_map(self):
        ''' Returns a dict of option->scoring for each input. '''
        scoring = self.default_scoring
        choices = dict([(choice, choice) for choice in scoring])
        scoring_map = {}

        for inputfield in self.inputfields:
            option_scoring = dict([(option['id'], {
                    'correctness': choices.get(option['choice']),
                    'points': scoring.get(option['choice'])
                }) for option in self._find_options(inputfield)])

            scoring_map[inputfield.get('id')] = option_scoring

        return scoring_map

    def _get_answer_map(self):
        ''' Returns a dict of answers for each input.'''
        answer_map = {}
        for inputfield in self.inputfields:
            correct_option = self._find_option_with_choice(
                inputfield, 'correct')
            if correct_option is not None:
                input_id = inputfield.get('id')
                answer_map[input_id] = correct_option.get('description')
        return answer_map

    def _get_max_points(self):
        ''' Returns a dict of the max points for each input: input id -> maxpoints. '''
        scoring = self.default_scoring
        correct_points = scoring.get('correct')
        return dict([(inputfield.get('id'), correct_points) for inputfield in self.inputfields])

    def _find_options(self, inputfield):
        ''' Returns an array of dicts where each dict represents an option. '''
        elements = inputfield.findall('./options/option')
        return [{
                'id': index,
                'description': option.text,
                'choice': option.get('choice')
                } for (index, option) in enumerate(elements)]

    def _find_option_with_choice(self, inputfield, choice):
        ''' Returns the option with the given choice value, otherwise None. '''
        for option in self._find_options(inputfield):
            if option['choice'] == choice:
                return option

    def _unpack(self, json_value):
        ''' Unpacks a student response value submitted as JSON.'''
        d = json.loads(json_value)
        if type(d) != dict:
            d = {}

        comment_value = d.get('comment', '')
        if not isinstance(d, basestring):
            comment_value = ''

        options_value = d.get('options', [])
        if not isinstance(options_value, list):
            options_value = []

        return {
            'options_value': options_value,
            'comment_value': comment_value
        }

    def _get_submitted_option_id(self, student_answer):
        ''' Return the single option that was selected, otherwise None.'''
        submitted = self._unpack(student_answer)
        option_ids = submitted['options_value']
        if len(option_ids) == 1:
            return option_ids[0]
        return None


class ChoiceTextResponse(LoncapaResponse):
    """
    Allows for multiple choice responses with text inputs
    Desired semantics match those of NumericalResponse and
    ChoiceResponse.
    """

    response_tag = 'choicetextresponse'
    max_inputfields = 1
    allowed_inputfields = ['choicetextgroup',
                           'checkboxtextgroup',
                           'radiotextgroup'
                           ]

    def setup_response(self):
        """
        Sets up three dictionaries for use later:
        `correct_choices`: These are the correct binary choices(radio/checkbox)
        `correct_inputs`: These are the numerical/string answers for required
        inputs.
        `answer_values`: This is a dict, keyed by the name of the binary choice
            which contains the correct answers for the text inputs separated by
            commas e.g. "1, 0.5"

        `correct_choices` and `correct_inputs` are used for grading the problem
        and `answer_values` is used for displaying correct answers.

        """
        context = self.context
        self.correct_choices = {}
        self.assign_choice_names()
        self.correct_inputs = {}
        self.answer_values = {self.answer_id: []}
        correct_xml = self.xml.xpath('//*[@id=$id]//choice[@correct="true"]',
                                     id=self.xml.get('id'))
        for node in correct_xml:
            # For each correct choice, set the `parent_name` to the
            # current choice's name
            parent_name = node.get('name')
            # Add the name of the correct binary choice to the
            # correct choices list as a key. The value is not important.
            self.correct_choices[parent_name] = {'answer': ''}
            # Add the name of the parent to the list of correct answers
            self.answer_values[self.answer_id].append(parent_name)
            answer_list = []
            # Loop over <numtolerance_input> elements inside of the correct choices
            for child in node:
                answer = child.get('answer', None)
                if not answer:
                    # If the question creator does not specify an answer for a
                    # <numtolerance_input> inside of a correct choice, raise an error
                    raise LoncapaProblemError(
                        "Answer not provided for numtolerance_input"
                    )
                # Contextualize the answer to allow script generated answers.
                answer = contextualize_text(answer, context)
                input_name = child.get('name')
                # Contextualize the tolerance to value.
                tolerance = contextualize_text(
                    child.get('tolerance', '0'),
                    context
                )
                # Add the answer and tolerance information for the current
                # numtolerance_input to `correct_inputs`
                self.correct_inputs[input_name] = {
                    'answer': answer,
                    'tolerance': tolerance
                }
                # Add the correct answer for this input to the list for show
                answer_list.append(answer)
            # Turn the list of numtolerance_input answers into a comma separated string.
            self.answer_values[parent_name] = ', '.join(answer_list)
        # Turn correct choices into a set. Allows faster grading.
        self.correct_choices = set(self.correct_choices.keys())

    def assign_choice_names(self):
        """
        Initialize name attributes in <choice> and <numtolerance_input> tags
        for this response.

        Example:
        Assuming for simplicity that `self.answer_id` = '1_2_1'

        Before the function is called `self.xml` =
        <radiotextgroup>
            <choice correct = "true">
                The number
                    <numtolerance_input answer="5"/>
                Is the mean of the list.
            </choice>
            <choice correct = "false">
                False demonstration choice
            </choice>
        </radiotextgroup>

        After this is called the choices and numtolerance_inputs will have a name
        attribute initialized and self.xml will be:

        <radiotextgroup>
        <choice correct = "true" name ="1_2_1_choiceinput_0bc">
            The number
                <numtolerance_input name = "1_2_1_choiceinput0_numtolerance_input_0"
                 answer="5"/>
            Is the mean of the list.
        </choice>
        <choice correct = "false" name = "1_2_1_choiceinput_1bc>
            False demonstration choice
        </choice>
        </radiotextgroup>
        """

        for index, choice in enumerate(
            self.xml.xpath('//*[@id=$id]//choice', id=self.xml.get('id'))
        ):
            # Set the name attribute for <choices>
            # "bc" is appended at the end to indicate that this is a
            # binary choice as opposed to a numtolerance_input, this convention
            # is used when grading the problem
            choice.set(
                "name",
                self.answer_id + "_choiceinput_" + str(index) + "bc"
            )
            # Set Name attributes for <numtolerance_input> elements
            # Look for all <numtolerance_inputs> inside this choice.
            numtolerance_inputs = choice.findall('numtolerance_input')
            # Look for all <decoy_input> inside this choice
            decoys = choice.findall('decoy_input')
            # <decoy_input> would only be used in choices which do not contain
            # <numtolerance_input>
            inputs = numtolerance_inputs if numtolerance_inputs else decoys
            # Give each input inside of the choice a name combining
            # The ordinality of the choice, and the ordinality of the input
            # within that choice e.g. 1_2_1_choiceinput_0_numtolerance_input_1
            for ind, child in enumerate(inputs):
                child.set(
                    "name",
                    self.answer_id + "_choiceinput_" + str(index) +
                    "_numtolerance_input_" + str(ind)
                )

    def get_score(self, student_answers):
        """
        Returns a `CorrectMap` showing whether `student_answers` are correct.

        `student_answers` contains keys for binary inputs(radiobutton,
        checkbox) and numerical inputs. Keys ending with 'bc' are binary
        choice inputs otherwise they are text fields.

        This method first separates the two
        types of answers and then grades them in separate methods.

        The student is only correct if they have both the binary inputs and
        numerical inputs correct.
        """
        answer_dict = student_answers.get(self.answer_id, "")
        binary_choices, numtolerance_inputs = self._split_answers_dict(answer_dict)
        # Check the binary choices first.
        choices_correct = self._check_student_choices(binary_choices)
        inputs_correct = self._check_student_inputs(numtolerance_inputs)
        # Only return correct if the student got both the binary
        # and numtolerance_inputs are correct
        correct = choices_correct and inputs_correct

        return CorrectMap(
            self.answer_id,
            'correct' if correct else 'incorrect'
        )

    def get_answers(self):
        """
        Returns a dictionary containing the names of binary choices as keys
        and a string of answers to any numtolerance_inputs which they may have
        e.g {choice_1bc : "answer1, answer2", choice_2bc : ""}
        """
        return self.answer_values

    def _split_answers_dict(self, a_dict):
        """
        Returns two dicts:
        `binary_choices` : dictionary {input_name: input_value} for
        the binary choices which the student selected.
        and
        `numtolerance_choices` : a dictionary {input_name: input_value}
        for the numtolerance_inputs inside of choices which were selected

        Determines if an input is inside of a binary input by looking at
        the beginning of it's name.

        For example. If a binary_choice was named '1_2_1_choiceinput_0bc'
        All of the numtolerance_inputs in it would have an idea that begins
        with '1_2_1_choice_input_0_numtolerance_input'

        Splits the name of the numtolerance_input at the occurence of
        '_numtolerance_input_' and appends 'bc' to the end to get the name
        of the choice it is contained in.

        Example:
        `a_dict` = {
            '1_2_1_choiceinput_0bc': '1_2_1_choiceinput_0bc',
            '1_2_1_choiceinput_0_numtolerance_input_0': '1',
            '1_2_1_choiceinput_0_numtolerance_input_1': '2'
            '1_2_1_choiceinput_1_numtolerance_input_0': '3'
        }

        In this case, the binary choice is '1_2_1_choiceinput_0bc', and
        the numtolerance_inputs associated with it are
        '1_2_1_choiceinput_0_numtolerance_input_0', and
        '1_2_1_choiceinput_0_numtolerance_input_1'.

        so the two return dictionaries would be
        `binary_choices` = {'1_2_1_choiceinput_0bc': '1_2_1_choiceinput_0bc'}
        and
        `numtolerance_choices` ={
            '1_2_1_choiceinput_0_numtolerance_input_0': '1',
            '1_2_1_choiceinput_0_numtolerance_input_1': '2'
        }

        The entry '1_2_1_choiceinput_1_numtolerance_input_0': '3' is discarded
        because it was not inside of a selected binary choice, and no validation
        should be performed on numtolerance_inputs inside of non-selected choices.
        """

        # Initialize the two dictionaries that are returned
        numtolerance_choices = {}
        binary_choices = {}

        # `selected_choices` is a list of binary choices which were "checked/selected"
        # when the student submitted the problem.
        # Keys in a_dict ending with 'bc' refer to binary choices.
        selected_choices = [key for key in a_dict if key.endswith("bc")]
        for key in selected_choices:
            binary_choices[key] = a_dict[key]

        # Convert the name of a numtolerance_input into the name of the binary
        # choice that it is contained within, and append it to the list if
        # the numtolerance_input's parent binary_choice is contained in
        # `selected_choices`.
        selected_numtolerance_inputs = [
            key for key in a_dict if key.partition("_numtolerance_input_")[0] + "bc"
            in selected_choices
        ]

        for key in selected_numtolerance_inputs:
            numtolerance_choices[key] = a_dict[key]

        return (binary_choices, numtolerance_choices)

    def _check_student_choices(self, choices):
        """
        Compares student submitted checkbox/radiobutton answers against
        the correct answers. Returns True or False.

        True if all of the correct choices are selected and no incorrect
        choices are selected.
        """
        student_choices = set(choices)
        required_selected = len(self.correct_choices - student_choices) == 0
        no_extra_selected = len(student_choices - self.correct_choices) == 0
        correct = required_selected and no_extra_selected
        return correct

    def _check_student_inputs(self, numtolerance_inputs):
        """
        Compares student submitted numerical answers against the correct
        answers and tolerances.

        `numtolerance_inputs` is a dictionary {answer_name : answer_value}

        Performs numerical validation by means of calling
        `compare_with_tolerance()` on all of `numtolerance_inputs`

        Performs a call to `compare_with_tolerance` even on values for
        decoy_inputs. This is used to validate their numericality and
        raise an error if the student entered a non numerical expression.

        Returns True if and only if all student inputs are correct.
        """
        inputs_correct = True
        for answer_name, answer_value in numtolerance_inputs.iteritems():
            # If `self.corrrect_inputs` does not contain an entry for
            # `answer_name`, this means that answer_name is a decoy
            # input's value, and validation of its numericality is the
            # only thing of interest from the later call to
            # `compare_with_tolerance`.
            params = self.correct_inputs.get(answer_name, {'answer': 0})

            correct_ans = params['answer']
            # Set the tolerance to '0' if it was not specified in the xml
            tolerance = params.get('tolerance', '0')
            # Make sure that the staff answer is a valid number
            try:
                correct_ans = complex(correct_ans)
            except ValueError:
                log.debug(
                    "Content error--answer" +
                    "'{0}' is not a valid complex number".format(correct_ans)
                )
                raise StudentInputError(
                    "The Staff answer could not be interpreted as a number."
                )
            # Compare the student answer to the staff answer/ or to 0
            # if all that is important is verifying numericality
            try:
                partial_correct = compare_with_tolerance(
                    evaluator(dict(), dict(), answer_value),
                    correct_ans,
                    tolerance
                )
            except:
                # Use the traceback-preserving version of re-raising with a
                # different type
                _, _, trace = sys.exc_info()

                raise StudentInputError(
                    "Could not interpret '{0}' as a number{1}".format(
                        cgi.escape(answer_value),
                        trace
                    )
                )
            # Ignore the results of the comparisons which were just for
            # Numerical Validation.
            if answer_name in self.correct_inputs and not partial_correct:
                # If any input is not correct, set the return value to False
                inputs_correct = False
        return inputs_correct

#-----------------------------------------------------------------------------

# TEMPORARY: List of all response subclasses
# FIXME: To be replaced by auto-registration

__all__ = [CodeResponse,
           NumericalResponse,
           FormulaResponse,
           CustomResponse,
           SchematicResponse,
           ExternalResponse,
           ImageResponse,
           OptionResponse,
           SymbolicResponse,
           StringResponse,
           ChoiceResponse,
           MultipleChoiceResponse,
           TrueFalseResponse,
           JavascriptResponse,
           AnnotationResponse,
           ChoiceTextResponse]
