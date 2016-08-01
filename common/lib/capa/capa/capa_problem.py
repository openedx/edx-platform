#
# File:   capa/capa_problem.py
#
# Nomenclature:
#
# A capa Problem is a collection of text and capa Response questions.
# Each Response may have one or more Input entry fields.
# The capa problem may include a solution.
#
"""
Main module which shows problems (of "capa" type).

This is used by capa_module.
"""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from gettext import gettext as _
import logging
import os.path
import re

from lxml import etree
from pytz import UTC
from xml.sax.saxutils import unescape

from capa.correctmap import CorrectMap
import capa.inputtypes as inputtypes
import capa.customrender as customrender
import capa.responsetypes as responsetypes
from capa.util import contextualize_text, convert_files_to_filenames
import capa.xqueue_interface as xqueue_interface
from capa.safe_exec import safe_exec


# extra things displayed after "show answers" is pressed
solution_tags = ['solution']

# fully accesible capa response types
ACCESSIBLE_CAPA_RESPONSE_TYPES = [
    'choiceresponse',
    'multiplechoiceresponse',
    'optionresponse',
    'numericalresponse',
    'stringresponse',
    'formularesponse',
]

# these get captured as student responses
response_properties = ["codeparam", "responseparam", "answer", "openendedparam"]

# special problem tags which should be turned into innocuous HTML
html_transforms = {
    'problem': {'tag': 'div'},
    'text': {'tag': 'span'},
    'math': {'tag': 'span'},
}

# These should be removed from HTML output, including all subelements
html_problem_semantics = [
    "codeparam",
    "responseparam",
    "answer",
    "script",
    "hintgroup",
    "openendedparam",
    "openendedrubric",
]

log = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
# main class for this module


DEFAULT_QUESTION_TEXT = _("You must specify meaningful question text.")


class LoncapaSystem(object):
    """
    An encapsulation of resources needed from the outside.

    These interfaces are collected here so that a caller of LoncapaProblem
    can provide these resources however make sense for their environment, and
    this code can remain independent.

    Attributes:
        i18n: an object implementing the `gettext.Translations` interface so
            that we can use `.ugettext` to localize strings.

    See :class:`ModuleSystem` for documentation of other attributes.

    """
    def __init__(                                       # pylint: disable=invalid-name
        self,
        ajax_url,
        anonymous_student_id,
        cache,
        can_execute_unsafe_code,
        get_python_lib_zip,
        DEBUG,                                          # pylint: disable=invalid-name
        filestore,
        i18n,
        node_path,
        render_template,
        seed,      # Why do we do this if we have self.seed?
        STATIC_URL,                                     # pylint: disable=invalid-name
        xqueue,
        matlab_api_key=None
    ):
        self.ajax_url = ajax_url
        self.anonymous_student_id = anonymous_student_id
        self.cache = cache
        self.can_execute_unsafe_code = can_execute_unsafe_code
        self.get_python_lib_zip = get_python_lib_zip
        self.DEBUG = DEBUG                              # pylint: disable=invalid-name
        self.filestore = filestore
        self.i18n = i18n
        self.node_path = node_path
        self.render_template = render_template
        self.seed = seed                     # Why do we do this if we have self.seed?
        self.STATIC_URL = STATIC_URL                    # pylint: disable=invalid-name
        self.xqueue = xqueue
        self.matlab_api_key = matlab_api_key


class LoncapaProblem(object):
    """
    Main class for capa Problems.
    """
    def __init__(self, problem_text, id, capa_system, capa_module,  # pylint: disable=redefined-builtin
                 state=None, seed=None):
        """
        Initializes capa Problem.

        Arguments:

            problem_text (string): xml defining the problem.
            id (string): identifier for this problem, often a filename (no spaces).
            capa_system (LoncapaSystem): LoncapaSystem instance which provides OS,
                rendering, user context, and other resources.
            capa_module: instance needed to access runtime/logging
            state (dict): containing the following keys:
                - `seed` (int) random number generator seed
                - `student_answers` (dict) maps input id to the stored answer for that input
                - `correct_map` (CorrectMap) a map of each input to their 'correctness'
                - `done` (bool) indicates whether or not this problem is considered done
                - `input_state` (dict) maps input_id to a dictionary that holds the state for that input
            seed (int): random number generator seed.

        """

        ## Initialize class variables from state
        self.do_reset()
        self.problem_id = id
        self.capa_system = capa_system
        self.capa_module = capa_module

        state = state or {}

        # Set seed according to the following priority:
        #       1. Contained in problem's state
        #       2. Passed into capa_problem via constructor
        self.seed = state.get('seed', seed)
        assert self.seed is not None, "Seed must be provided for LoncapaProblem."

        self.student_answers = state.get('student_answers', {})
        if 'correct_map' in state:
            self.correct_map.set_dict(state['correct_map'])
        self.done = state.get('done', False)
        self.input_state = state.get('input_state', {})

        # Convert startouttext and endouttext to proper <text></text>
        problem_text = re.sub(r"startouttext\s*/", "text", problem_text)
        problem_text = re.sub(r"endouttext\s*/", "/text", problem_text)
        self.problem_text = problem_text

        # parse problem XML file into an element tree
        self.tree = etree.XML(problem_text)

        self.make_xml_compatible(self.tree)

        # handle any <include file="foo"> tags
        self._process_includes()

        # construct script processor context (eg for customresponse problems)
        self.context = self._extract_context(self.tree)

        # Pre-parse the XML tree: modifies it to add ID's and perform some in-place
        # transformations.  This also creates the dict (self.responders) of Response
        # instances for each question in the problem. The dict has keys = xml subtree of
        # Response, values = Response instance
        self.problem_data = self._preprocess_problem(self.tree)

        if not self.student_answers:  # True when student_answers is an empty dict
            self.set_initial_display()

        # dictionary of InputType objects associated with this problem
        #   input_id string -> InputType object
        self.inputs = {}

        # Run response late_transforms last (see MultipleChoiceResponse)
        # Sort the responses to be in *_1 *_2 ... order.
        responses = self.responders.values()
        responses = sorted(responses, key=lambda resp: int(resp.id[resp.id.rindex('_') + 1:]))
        for response in responses:
            if hasattr(response, 'late_transforms'):
                response.late_transforms(self)

        self.extracted_tree = self._extract_html(self.tree)

    def make_xml_compatible(self, tree):
        """
        Adjust tree xml in-place for compatibility before creating
        a problem from it.
        The idea here is to provide a central point for XML translation,
        for example, supporting an old XML format. At present, there just two translations.

        1. <additional_answer> compatibility translation:
        old:    <additional_answer>ANSWER</additional_answer>
        convert to
        new:    <additional_answer answer="ANSWER">OPTIONAL-HINT</addional_answer>

        2. <optioninput> compatibility translation:
        optioninput works like this internally:
            <optioninput options="('yellow','blue','green')" correct="blue" />
        With extended hints there is a new <option> tag, like this
            <option correct="True">blue <optionhint>sky color</optionhint> </option>
        This translation takes in the new format and synthesizes the old option= attribute
        so all downstream logic works unchanged with the new <option> tag format.
        """
        additionals = tree.xpath('//stringresponse/additional_answer')
        for additional in additionals:
            answer = additional.get('answer')
            text = additional.text
            if not answer and text:  # trigger of old->new conversion
                additional.set('answer', text)
                additional.text = ''

        for optioninput in tree.xpath('//optioninput'):
            correct_option = None
            child_options = []
            for option_element in optioninput.findall('./option'):
                option_name = option_element.text.strip()
                if option_element.get('correct').upper() == 'TRUE':
                    correct_option = option_name
                child_options.append("'" + option_name + "'")

            if len(child_options) > 0:
                options_string = '(' + ','.join(child_options) + ')'
                optioninput.attrib.update({'options': options_string})
                if correct_option:
                    optioninput.attrib.update({'correct': correct_option})

    def do_reset(self):
        """
        Reset internal state to unfinished, with no answers
        """
        self.student_answers = dict()
        self.correct_map = CorrectMap()
        self.done = False

    def set_initial_display(self):
        """
        Set the student's answers to the responders' initial displays, if specified.
        """
        initial_answers = dict()
        for responder in self.responders.values():
            if hasattr(responder, 'get_initial_display'):
                initial_answers.update(responder.get_initial_display())

        self.student_answers = initial_answers

    def __unicode__(self):
        return u"LoncapaProblem ({0})".format(self.problem_id)

    def get_state(self):
        """
        Stored per-user session data neeeded to:
            1) Recreate the problem
            2) Populate any student answers.
        """

        return {'seed': self.seed,
                'student_answers': self.student_answers,
                'correct_map': self.correct_map.get_dict(),
                'input_state': self.input_state,
                'done': self.done}

    def get_max_score(self):
        """
        Return the maximum score for this problem.
        """
        maxscore = 0
        for responder in self.responders.values():
            maxscore += responder.get_max_score()
        return maxscore

    def get_score(self):
        """
        Compute score for this problem.  The score is the number of points awarded.
        Returns a dictionary {'score': integer, from 0 to get_max_score(),
                              'total': get_max_score()}.
        """
        correct = 0
        for key in self.correct_map:
            try:
                correct += self.correct_map.get_npoints(key)
            except Exception:
                log.error('key=%s, correct_map = %s', key, self.correct_map)
                raise

        if (not self.student_answers) or len(self.student_answers) == 0:
            return {'score': 0,
                    'total': self.get_max_score()}
        else:
            return {'score': correct,
                    'total': self.get_max_score()}

    def update_score(self, score_msg, queuekey):
        """
        Deliver grading response (e.g. from async code checking) to
            the specific ResponseType that requested grading

        Returns an updated CorrectMap
        """
        cmap = CorrectMap()
        cmap.update(self.correct_map)
        for responder in self.responders.values():
            if hasattr(responder, 'update_score'):
                # Each LoncapaResponse will update its specific entries in cmap
                #   cmap is passed by reference
                responder.update_score(score_msg, cmap, queuekey)
        self.correct_map.set_dict(cmap.get_dict())
        return cmap

    def ungraded_response(self, xqueue_msg, queuekey):
        """
        Handle any responses from the xqueue that do not contain grades
        Will try to pass the queue message to all inputtypes that can handle ungraded responses

        Does not return any value
        """
        # check against each inputtype
        for the_input in self.inputs.values():
            # if the input type has an ungraded function, pass in the values
            if hasattr(the_input, 'ungraded_response'):
                the_input.ungraded_response(xqueue_msg, queuekey)

    def is_queued(self):
        """
        Returns True if any part of the problem has been submitted to an external queue
        (e.g. for grading.)
        """
        return any(self.correct_map.is_queued(answer_id) for answer_id in self.correct_map)

    def get_recentmost_queuetime(self):
        """
        Returns a DateTime object that represents the timestamp of the most recent
        queueing request, or None if not queued
        """
        if not self.is_queued():
            return None

        # Get a list of timestamps of all queueing requests, then convert it to a DateTime object
        queuetime_strs = [
            self.correct_map.get_queuetime_str(answer_id)
            for answer_id in self.correct_map
            if self.correct_map.is_queued(answer_id)
        ]
        queuetimes = [
            datetime.strptime(qt_str, xqueue_interface.dateformat).replace(tzinfo=UTC)
            for qt_str in queuetime_strs
        ]

        return max(queuetimes)

    def grade_answers(self, answers):
        """
        Grade student responses.  Called by capa_module.check_problem.

        `answers` is a dict of all the entries from request.POST, but with the first part
        of each key removed (the string before the first "_").

        Thus, for example, input_ID123 -> ID123, and input_fromjs_ID123 -> fromjs_ID123

        Calls the Response for each question in this problem, to do the actual grading.
        """

        # if answers include File objects, convert them to filenames.
        self.student_answers = convert_files_to_filenames(answers)
        return self._grade_answers(answers)

    def supports_rescoring(self):
        """
        Checks that the current problem definition permits rescoring.

        More precisely, it checks that there are no response types in
        the current problem that are not fully supported (yet) for rescoring.

        This includes responsetypes for which the student's answer
        is not properly stored in state, i.e. file submissions.  At present,
        we have no way to know if an existing response was actually a real
        answer or merely the filename of a file submitted as an answer.

        It turns out that because rescoring is a background task, limiting
        it to responsetypes that don't support file submissions also means
        that the responsetypes are synchronous.  This is convenient as it
        permits rescoring to be complete when the rescoring call returns.
        """
        return all('filesubmission' not in responder.allowed_inputfields for responder in self.responders.values())

    def rescore_existing_answers(self):
        """
        Rescore student responses.  Called by capa_module.rescore_problem.
        """
        return self._grade_answers(None)

    def _grade_answers(self, student_answers):
        """
        Internal grading call used for checking new 'student_answers' and also
        rescoring existing student_answers.

        For new student_answers being graded, `student_answers` is a dict of all the
        entries from request.POST, but with the first part of each key removed
        (the string before the first "_").  Thus, for example,
        input_ID123 -> ID123, and input_fromjs_ID123 -> fromjs_ID123.

        For rescoring, `student_answers` is None.

        Calls the Response for each question in this problem, to do the actual grading.
        """
        # old CorrectMap
        oldcmap = self.correct_map

        # start new with empty CorrectMap
        newcmap = CorrectMap()
        # Call each responsetype instance to do actual grading
        for responder in self.responders.values():
            # File objects are passed only if responsetype explicitly allows
            # for file submissions.  But we have no way of knowing if
            # student_answers contains a proper answer or the filename of
            # an earlier submission, so for now skip these entirely.
            # TODO: figure out where to get file submissions when rescoring.
            if 'filesubmission' in responder.allowed_inputfields and student_answers is None:
                _ = self.capa_system.i18n.ugettext
                raise Exception(_(u"Cannot rescore problems with possible file submissions"))

            # use 'student_answers' only if it is provided, and if it might contain a file
            # submission that would not exist in the persisted "student_answers".
            if 'filesubmission' in responder.allowed_inputfields and student_answers is not None:
                results = responder.evaluate_answers(student_answers, oldcmap)
            else:
                results = responder.evaluate_answers(self.student_answers, oldcmap)
            newcmap.update(results)

        self.correct_map = newcmap
        return newcmap

    def get_question_answers(self):
        """
        Returns a dict of answer_ids to answer values. If we cannot generate
        an answer (this sometimes happens in customresponses), that answer_id is
        not included. Called by "show answers" button JSON request
        (see capa_module)
        """
        # dict of (id, correct_answer)
        answer_map = dict()
        for response in self.responders.keys():
            results = self.responder_answers[response]
            answer_map.update(results)

        # include solutions from <solution>...</solution> stanzas
        for entry in self.tree.xpath("//" + "|//".join(solution_tags)):
            answer = etree.tostring(entry)
            if answer:
                answer_map[entry.get('id')] = contextualize_text(answer, self.context)

        log.debug('answer_map = %s', answer_map)
        return answer_map

    def get_answer_ids(self):
        """
        Return the IDs of all the responses -- these are the keys used for
        the dicts returned by grade_answers and get_question_answers. (Though
        get_question_answers may only return a subset of these.
        """
        answer_ids = []
        for response in self.responders.keys():
            results = self.responder_answers[response]
            answer_ids.append(results.keys())
        return answer_ids

    def do_targeted_feedback(self, tree):
        """
        Implements targeted-feedback in-place on  <multiplechoiceresponse> --
        choice-level explanations shown to a student after submission.
        Does nothing if there is no targeted-feedback attribute.
        """
        # Note that the modifications has been done, avoiding problems if called twice.
        if hasattr(self, 'has_targeted'):
            return
        self.has_targeted = True  # pylint: disable=attribute-defined-outside-init

        for mult_choice_response in tree.xpath('//multiplechoiceresponse[@targeted-feedback]'):
            show_explanation = mult_choice_response.get('targeted-feedback') == 'alwaysShowCorrectChoiceExplanation'

            # Grab the first choicegroup (there should only be one within each <multiplechoiceresponse> tag)
            choicegroup = mult_choice_response.xpath('./choicegroup[@type="MultipleChoice"]')[0]
            choices_list = list(choicegroup.iter('choice'))

            # Find the student answer key that matches our <choicegroup> id
            student_answer = self.student_answers.get(choicegroup.get('id'))
            expl_id_for_student_answer = None

            # Keep track of the explanation-id that corresponds to the student's answer
            # Also, keep track of the solution-id
            solution_id = None
            for choice in choices_list:
                if choice.get('name') == student_answer:
                    expl_id_for_student_answer = choice.get('explanation-id')
                if choice.get('correct') == 'true':
                    solution_id = choice.get('explanation-id')

            # Filter out targetedfeedback that doesn't correspond to the answer the student selected
            # Note: following-sibling will grab all following siblings, so we just want the first in the list
            targetedfeedbackset = mult_choice_response.xpath('./following-sibling::targetedfeedbackset')
            if len(targetedfeedbackset) != 0:
                targetedfeedbackset = targetedfeedbackset[0]
                targetedfeedbacks = targetedfeedbackset.xpath('./targetedfeedback')
                for targetedfeedback in targetedfeedbacks:
                    # Don't show targeted feedback if the student hasn't answer the problem
                    # or if the target feedback doesn't match the student's (incorrect) answer
                    if not self.done or targetedfeedback.get('explanation-id') != expl_id_for_student_answer:
                        targetedfeedbackset.remove(targetedfeedback)

            # Do not displace the solution under these circumstances
            if not show_explanation or not self.done:
                continue

            # The next element should either be <solution> or <solutionset>
            next_element = targetedfeedbackset.getnext()
            parent_element = tree
            solution_element = None
            if next_element is not None and next_element.tag == 'solution':
                solution_element = next_element
            elif next_element is not None and next_element.tag == 'solutionset':
                solutions = next_element.xpath('./solution')
                for solution in solutions:
                    if solution.get('explanation-id') == solution_id:
                        parent_element = next_element
                        solution_element = solution

            # If could not find the solution element, then skip the remaining steps below
            if solution_element is None:
                continue

            # Change our correct-choice explanation from a "solution explanation" to within
            # the set of targeted feedback, which means the explanation will render on the page
            # without the student clicking "Show Answer" or seeing a checkmark next to the correct choice
            parent_element.remove(solution_element)

            # Add our solution instead to the targetedfeedbackset and change its tag name
            solution_element.tag = 'targetedfeedback'
            targetedfeedbackset.append(solution_element)

    def get_html(self):
        """
        Main method called externally to get the HTML to be rendered for this capa Problem.
        """
        self.do_targeted_feedback(self.tree)
        html = contextualize_text(etree.tostring(self._extract_html(self.tree)), self.context)
        return html

    def handle_input_ajax(self, data):
        """
        InputTypes can support specialized AJAX calls. Find the correct input and pass along the correct data

        Also, parse out the dispatch from the get so that it can be passed onto the input type nicely
        """

        # pull out the id
        input_id = data['input_id']
        if self.inputs[input_id]:
            dispatch = data['dispatch']
            return self.inputs[input_id].handle_ajax(dispatch, data)
        else:
            log.warning("Could not find matching input for id: %s", input_id)
            return {}

    # ======= Private Methods Below ========

    def _process_includes(self):
        """
        Handle any <include file="foo"> tags by reading in the specified file and inserting it
        into our XML tree.  Fail gracefully if debugging.
        """
        includes = self.tree.findall('.//include')
        for inc in includes:
            filename = inc.get('file')
            if filename is not None:
                try:
                    # open using LoncapaSystem OSFS filestore
                    ifp = self.capa_system.filestore.open(filename)
                except Exception as err:
                    log.warning(
                        'Error %s in problem xml include: %s',
                        err,
                        etree.tostring(inc, pretty_print=True)
                    )
                    log.warning(
                        'Cannot find file %s in %s', filename, self.capa_system.filestore
                    )
                    # if debugging, don't fail - just log error
                    # TODO (vshnayder): need real error handling, display to users
                    if not self.capa_system.DEBUG:
                        raise
                    else:
                        continue
                try:
                    # read in and convert to XML
                    incxml = etree.XML(ifp.read())
                except Exception as err:
                    log.warning(
                        'Error %s in problem xml include: %s',
                        err,
                        etree.tostring(inc, pretty_print=True)
                    )
                    log.warning('Cannot parse XML in %s', (filename))
                    # if debugging, don't fail - just log error
                    # TODO (vshnayder): same as above
                    if not self.capa_system.DEBUG:
                        raise
                    else:
                        continue

                # insert new XML into tree in place of include
                parent = inc.getparent()
                parent.insert(parent.index(inc), incxml)
                parent.remove(inc)
                log.debug('Included %s into %s', filename, self.problem_id)

    def _extract_system_path(self, script):
        """
        Extracts and normalizes additional paths for code execution.
        For now, there's a default path of data/course/code; this may be removed
        at some point.

        script : ?? (TODO)
        """

        DEFAULT_PATH = ['code']

        # Separate paths by :, like the system path.
        raw_path = script.get('system_path', '').split(":") + DEFAULT_PATH

        # find additional comma-separated modules search path
        path = []

        for dir in raw_path:
            if not dir:
                continue

            # path is an absolute path or a path relative to the data dir
            dir = os.path.join(self.capa_system.filestore.root_path, dir)
            # Check that we are within the filestore tree.
            reldir = os.path.relpath(dir, self.capa_system.filestore.root_path)
            if ".." in reldir:
                log.warning("Ignoring Python directory outside of course: %r", dir)
                continue

            abs_dir = os.path.normpath(dir)
            path.append(abs_dir)

        return path

    def _extract_context(self, tree):
        """
        Extract content of <script>...</script> from the problem.xml file, and exec it in the
        context of this problem.  Provides ability to randomize problems, and also set
        variables for problem answer checking.

        Problem XML goes to Python execution context. Runs everything in script tags.
        """
        context = {}
        context['seed'] = self.seed
        context['anonymous_student_id'] = self.capa_system.anonymous_student_id
        all_code = ''

        python_path = []

        for script in tree.findall('.//script'):

            stype = script.get('type')
            if stype:
                if 'javascript' in stype:
                    continue    # skip javascript
                if 'perl' in stype:
                    continue        # skip perl
            # TODO: evaluate only python

            for d in self._extract_system_path(script):
                if d not in python_path and os.path.exists(d):
                    python_path.append(d)

            XMLESC = {"&apos;": "'", "&quot;": '"'}
            code = unescape(script.text, XMLESC)
            all_code += code

        extra_files = []
        if all_code:
            # An asset named python_lib.zip can be imported by Python code.
            zip_lib = self.capa_system.get_python_lib_zip()
            if zip_lib is not None:
                extra_files.append(("python_lib.zip", zip_lib))
                python_path.append("python_lib.zip")

            try:
                safe_exec(
                    all_code,
                    context,
                    random_seed=self.seed,
                    python_path=python_path,
                    extra_files=extra_files,
                    cache=self.capa_system.cache,
                    slug=self.problem_id,
                    unsafely=self.capa_system.can_execute_unsafe_code(),
                )
            except Exception as err:
                log.exception("Error while execing script code: " + all_code)
                msg = "Error while executing script code: %s" % str(err).replace('<', '&lt;')
                raise responsetypes.LoncapaProblemError(msg)

        # Store code source in context, along with the Python path needed to run it correctly.
        context['script_code'] = all_code
        context['python_path'] = python_path
        context['extra_files'] = extra_files or None
        return context

    def _extract_html(self, problemtree):  # private
        """
        Main (private) function which converts Problem XML tree to HTML.
        Calls itself recursively.

        Returns Element tree of XHTML representation of problemtree.
        Calls render_html of Response instances to render responses into XHTML.

        Used by get_html.
        """
        if not isinstance(problemtree.tag, basestring):
            # Comment and ProcessingInstruction nodes are not Elements,
            # and we're ok leaving those behind.
            # BTW: etree gives us no good way to distinguish these things
            # other than to examine .tag to see if it's a string. :(
            return

        if (problemtree.tag == 'script' and problemtree.get('type')
                and 'javascript' in problemtree.get('type')):
            # leave javascript intact.
            return deepcopy(problemtree)

        if problemtree.tag in html_problem_semantics:
            return

        problemid = problemtree.get('id')    # my ID

        if problemtree.tag in inputtypes.registry.registered_tags():
            # If this is an inputtype subtree, let it render itself.
            response_id = self.problem_id + '_' + problemtree.get('response_id')
            response_data = self.problem_data[response_id]

            status = 'unsubmitted'
            msg = ''
            hint = ''
            hintmode = None
            input_id = problemtree.get('id')
            answervariable = None
            if problemid in self.correct_map:
                pid = input_id
                status = self.correct_map.get_correctness(pid)
                msg = self.correct_map.get_msg(pid)
                hint = self.correct_map.get_hint(pid)
                hintmode = self.correct_map.get_hintmode(pid)
                answervariable = self.correct_map.get_property(pid, 'answervariable')

            value = ''
            if self.student_answers and problemid in self.student_answers:
                value = self.student_answers[problemid]

            if input_id not in self.input_state:
                self.input_state[input_id] = {}

            # do the rendering
            state = {
                'value': value,
                'status': status,
                'id': input_id,
                'input_state': self.input_state[input_id],
                'answervariable': answervariable,
                'response_data': response_data,
                'feedback': {
                    'message': msg,
                    'hint': hint,
                    'hintmode': hintmode,
                }
            }

            input_type_cls = inputtypes.registry.get_class_for_tag(problemtree.tag)
            # save the input type so that we can make ajax calls on it if we need to
            self.inputs[input_id] = input_type_cls(self.capa_system, problemtree, state)
            return self.inputs[input_id].get_html()

        # let each Response render itself
        if problemtree in self.responders:
            overall_msg = self.correct_map.get_overall_message()
            return self.responders[problemtree].render_html(
                self._extract_html, response_msg=overall_msg
            )

        # let each custom renderer render itself:
        if problemtree.tag in customrender.registry.registered_tags():
            renderer_class = customrender.registry.get_class_for_tag(problemtree.tag)
            renderer = renderer_class(self.capa_system, problemtree)
            return renderer.get_html()

        # otherwise, render children recursively, and copy over attributes
        tree = etree.Element(problemtree.tag)
        for item in problemtree:
            item_xhtml = self._extract_html(item)
            if item_xhtml is not None:
                tree.append(item_xhtml)

        if tree.tag in html_transforms:
            tree.tag = html_transforms[problemtree.tag]['tag']
        else:
            # copy attributes over if not innocufying
            for (key, value) in problemtree.items():
                tree.set(key, value)

        tree.text = problemtree.text
        tree.tail = problemtree.tail

        return tree

    def _preprocess_problem(self, tree):  # private
        """
        Assign IDs to all the responses
        Assign sub-IDs to all entries (textline, schematic, etc.)
        Annoted correctness and value
        In-place transformation

        Also create capa Response instances for each responsetype and save as self.responders

        Obtain all responder answers and save as self.responder_answers dict (key = response)
        """
        response_id = 1
        problem_data = {}
        self.responders = {}
        for response in tree.xpath('//' + "|//".join(responsetypes.registry.registered_tags())):
            response_id_str = self.problem_id + "_" + str(response_id)
            # create and save ID for this response
            response.set('id', response_id_str)
            response_id += 1

            answer_id = 1
            input_tags = inputtypes.registry.registered_tags()
            inputfields = tree.xpath(
                "|".join(['//' + response.tag + '[@id=$id]//' + x for x in input_tags]),
                id=response_id_str
            )

            # assign one answer_id for each input type
            for entry in inputfields:
                entry.attrib['response_id'] = str(response_id)
                entry.attrib['answer_id'] = str(answer_id)
                entry.attrib['id'] = "%s_%i_%i" % (self.problem_id, response_id, answer_id)
                answer_id = answer_id + 1

            question_id = self.problem_id + '_' + str(response_id)
            label = ''
            element_to_be_deleted = None

            # Extract label value from <label> tag or label attribute from inside the responsetype
            responsetype_label_tag = response.find('label')
            if responsetype_label_tag is not None:
                label = responsetype_label_tag.text
                # Delete <label> tag containing question text otherwise question will be rendered twice
                element_to_be_deleted = responsetype_label_tag
            elif 'label' in inputfields[0].attrib:
                # Extract label value from label attribute
                # This is the case when we have a problem
                # * with multiple questions without separation
                # * single question with old XML format only

                label = inputfields[0].attrib['label']
                # Get first <p> tag before responsetype
                p_tag = response.xpath('preceding-sibling::p[1]')

                if p_tag:
                    # It may be possible that label attribute value doesn't match with <p> tag
                    # This happens when author updated the question <p> tag directly in XML but
                    # didn't changed the label attribute value. In this case we will consider the
                    # first <p> tag before responsetype as question.
                    if label != p_tag[0].text:
                        label = p_tag[0].text
                    element_to_be_deleted = p_tag[0]
            else:
                # neither <label> tag nor label attribute is present inside responsetype
                # This is the case when we have a problem with multi-questions without --- having markdown
                # find the immediate <label> tag before the responsetype. also delete it avoid rendering twice
                label_tag = response.xpath("preceding-sibling::label[1]")
                if label_tag:
                    label = label_tag[0].text
                    element_to_be_deleted = label_tag[0]

            label = label.strip() or DEFAULT_QUESTION_TEXT

            # delete label or p element only if responsetype is fully accessible
            if response.tag in ACCESSIBLE_CAPA_RESPONSE_TYPES and element_to_be_deleted is not None:
                element_to_be_deleted.getparent().remove(element_to_be_deleted)

            # for non-accessible responsetypes it may be possible that label attribute is not present
            # in this case pass an empty label. remember label attribute is only used as value for aria-label
            if response.tag not in ACCESSIBLE_CAPA_RESPONSE_TYPES and label == DEFAULT_QUESTION_TEXT:
                label = ''

            # Extract descriptions and set unique id on each description tag
            description_tags = response.findall('description')
            description_id = 1
            descriptions = OrderedDict()
            for description in description_tags:
                descriptions[
                    "%s_description_%i_%i" % (self.problem_id, response_id, description_id)
                ] = description.text
                response.remove(description)
                description_id += 1

            problem_data[question_id] = {
                'label': label,
                'description_ids': ' '.join(descriptions.keys()),
                'descriptions': descriptions
            }

            # instantiate capa Response
            responsetype_cls = responsetypes.registry.get_class_for_tag(response.tag)
            responder = responsetype_cls(response, inputfields, self.context, self.capa_system, self.capa_module)
            # save in list in self
            self.responders[response] = responder

        # get responder answers (do this only once, since there may be a performance cost,
        # eg with externalresponse)
        self.responder_answers = {}
        for response in self.responders.keys():
            try:
                self.responder_answers[response] = self.responders[response].get_answers()
            except:
                log.debug('responder %s failed to properly return get_answers()',
                          self.responders[response])  # FIXME
                raise

        # <solution>...</solution> may not be associated with any specific response; give
        # IDs for those separately
        # TODO: We should make the namespaces consistent and unique (e.g. %s_problem_%i).
        solution_id = 1
        for solution in tree.findall('.//solution'):
            solution.attrib['id'] = "%s_solution_%i" % (self.problem_id, solution_id)
            solution_id += 1

        return problem_data
