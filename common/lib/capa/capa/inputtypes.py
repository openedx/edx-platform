#
# File:   courseware/capa/inputtypes.py
#

"""
Module containing the problem elements which render into input objects

- textline
- textbox (aka codeinput)
- schematic
- choicegroup (aka radiogroup, checkboxgroup)
- javascriptinput
- imageinput  (for clickable image)
- optioninput (for option list)
- filesubmission (upload a file)
- crystallography
- vsepr_input
- drag_and_drop
- formulaequationinput
- chemicalequationinput

These are matched by *.html files templates/*.html which are mako templates with the
actual html.

Each input type takes the xml tree as 'element', the previous answer as 'value', and the
graded status as'status'
"""

# TODO: make hints do something

# TODO: make all inputtypes actually render msg

# TODO: remove unused fields (e.g. 'hidden' in a few places)

# TODO: add validators so that content folks get better error messages.


# Possible todo: make inline the default for textlines and other "one-line" inputs.  It probably
# makes sense, but a bunch of problems have markup that assumes block.  Bigger TODO: figure out a
# general css and layout strategy for capa, document it, then implement it.

import time
import json
import logging
from lxml import etree
import re
import shlex  # for splitting quoted strings
import sys
import pyparsing
import html5lib
import bleach

from .util import sanitize_html
from .registry import TagRegistry
from chem import chemcalc
from calc.preview import latex_preview
import xqueue_interface
from xqueue_interface import XQUEUE_TIMEOUT
from datetime import datetime
from xmodule.stringify import stringify_children

log = logging.getLogger(__name__)

#########################################################################

registry = TagRegistry()  # pylint: disable=invalid-name


class Status(object):
    """
    Problem status
    attributes: classname, display_name, display_tooltip
    """
    css_classes = {
        # status: css class
        'unsubmitted': 'unanswered',
        'incomplete': 'incorrect',
        'queued': 'processing',
    }
    __slots__ = ('classname', '_status', 'display_name', 'display_tooltip')

    def __init__(self, status, gettext_func=unicode):
        self.classname = self.css_classes.get(status, status)
        _ = gettext_func
        names = {
            'correct': _('correct'),
            'incorrect': _('incorrect'),
            'partially-correct': _('partially correct'),
            'incomplete': _('incomplete'),
            'unanswered': _('unanswered'),
            'unsubmitted': _('unanswered'),
            'queued': _('processing'),
        }
        tooltips = {
            # Translators: these are tooltips that indicate the state of an assessment question
            'correct': _('This answer is correct.'),
            'incorrect': _('This answer is incorrect.'),
            'partially-correct': _('This answer is partially correct.'),
            'unanswered': _('This answer is unanswered.'),
            'unsubmitted': _('This answer is unanswered.'),
            'queued': _('This answer is being processed.'),
        }
        self.display_name = names.get(status, unicode(status))
        self.display_tooltip = tooltips.get(status, u'')
        self._status = status or ''

    def __str__(self):
        return self._status

    def __unicode__(self):
        return self._status.decode('utf8')

    def __repr__(self):
        return 'Status(%r)' % self._status

    def __eq__(self, other):
        return self._status == str(other)


class Attribute(object):
    """
    Allows specifying required and optional attributes for input types.
    """

    # want to allow default to be None, but also allow required objects
    _sentinel = object()

    def __init__(self, name, default=_sentinel, transform=None, validate=None, render=True):
        """
        Define an attribute

        name (str): then name of the attribute--should be alphanumeric (valid for an XML attribute)

        default (any type): If not specified, this attribute is required.  If specified, use this as the default value
                        if the attribute is not specified.  Note that this value will not be transformed or validated.

        transform (function str -> any type): If not None, will be called to transform the parsed value into an internal
                        representation.

        validate (function str-or-return-type-of-tranform -> unit or exception): If not None, called to validate the
                       (possibly transformed) value of the attribute.  Should raise ValueError with a helpful message if
                       the value is invalid.

        render (bool): if False, don't include this attribute in the template context.
        """
        self.name = name
        self.default = default
        self.validate = validate
        self.transform = transform
        self.render = render

    def parse_from_xml(self, element):
        """
        Given an etree xml element that should have this attribute, do the obvious thing:
          - look for it.  raise ValueError if not found and required.
          - transform and validate.  pass through any exceptions from transform or validate.
        """
        val = element.get(self.name)
        if self.default == self._sentinel and val is None:
            raise ValueError(
                'Missing required attribute {0}.'.format(self.name)
            )

        if val is None:
            # not required, so return default
            return self.default

        if self.transform is not None:
            val = self.transform(val)

        if self.validate is not None:
            self.validate(val)

        return val


class InputTypeBase(object):
    """
    Abstract base class for input types.
    """

    template = None

    def __init__(self, system, xml, state):
        """
        Instantiate an InputType class.  Arguments:

        - system    : LoncapaModule instance which provides OS, rendering, and user context.
                      Specifically, must have a render_template function.
        - xml       : Element tree of this Input element
        - state     : a dictionary with optional keys:
                      * 'value'  -- the current value of this input
                                    (what the student entered last time)
                      * 'id' -- the id of this input, typically
                                "{problem-location}_{response-num}_{input-num}"
                      * 'status' (answered, unanswered, unsubmitted)
                      * 'input_state' -- dictionary containing any inputtype-specific state
                                        that has been preserved
                      * 'feedback' (dictionary containing keys for hints, errors, or other
                         feedback from previous attempt.  Specifically 'message', 'hint',
                         'hintmode'.  If 'hintmode' is 'always', the hint is always displayed.)
        """

        self.xml = xml
        self.tag = xml.tag
        self.capa_system = system

        # NOTE: ID should only come from one place.  If it comes from multiple,
        # we use state first, XML second (in case the xml changed, but we have
        # existing state with an old id). Since we don't make this guarantee,
        # we can swap this around in the future if there's a more logical
        # order.

        self.input_id = state.get('id', xml.get('id'))
        if self.input_id is None:
            raise ValueError(
                "input id state is None. xml is {0}".format(etree.tostring(xml))
            )

        self.value = state.get('value', '')

        feedback = state.get('feedback', {})
        self.msg = feedback.get('message', '')
        self.hint = feedback.get('hint', '')
        self.hintmode = feedback.get('hintmode', None)
        self.input_state = state.get('input_state', {})
        self.answervariable = state.get('answervariable', None)
        self.response_data = state.get('response_data')

        # put hint above msg if it should be displayed
        if self.hintmode == 'always':
            self.msg = self.hint + ('<br/>' if self.msg else '') + self.msg

        self.status = state.get('status', 'unanswered')

        try:
            # Pre-parse and process all the declared requirements.
            self.process_requirements()

            # Call subclass "constructor" -- means they don't have to worry about calling
            # super().__init__, and are isolated from changes to the input
            # constructor interface.
            self.setup()
        except Exception as err:
            # Something went wrong: add xml to message, but keep the traceback
            msg = u"Error in xml '{x}': {err} ".format(
                x=etree.tostring(xml), err=err.message)
            raise Exception, msg, sys.exc_info()[2]

    @classmethod
    def get_attributes(cls):
        """
        Should return a list of Attribute objects (see docstring there for details). Subclasses should override.  e.g.

        return [Attribute('unicorn', True), Attribute('num_dragons', 12, transform=int), ...]
        """
        return []

    def process_requirements(self):
        """
        Subclasses can declare lists of required and optional attributes.  This
        function parses the input xml and pulls out those attributes.  This
        isolates most simple input types from needing to deal with xml parsing at all.

        Processes attributes, putting the results in the self.loaded_attributes dictionary.  Also creates a set
        self.to_render, containing the names of attributes that should be included in the context by default.
        """
        # Use local dicts and sets so that if there are exceptions, we don't
        # end up in a partially-initialized state.
        loaded = {}
        to_render = set()
        for attribute in self.get_attributes():
            loaded[attribute.name] = attribute.parse_from_xml(self.xml)
            if attribute.render:
                to_render.add(attribute.name)

        self.loaded_attributes = loaded
        self.to_render = to_render

    def setup(self):
        """
        InputTypes should override this to do any needed initialization.  It is called after the
        constructor, so all base attributes will be set.

        If this method raises an exception, it will be wrapped with a message that includes the
        problem xml.
        """
        pass

    def handle_ajax(self, dispatch, data):
        """
        InputTypes that need to handle specialized AJAX should override this.

        Input:
            dispatch: a string that can be used to determine how to handle the data passed in
            data: a dictionary containing the data that was sent with the ajax call

        Output:
            a dictionary object that can be serialized into JSON. This will be sent back to the Javascript.
        """
        pass

    def _get_render_context(self):
        """
        Should return a dictionary of keys needed to render the template for the input type.

        (Separate from get_html to faciliate testing of logic separately from the rendering)

        The default implementation gets the following rendering context: basic things like value, id, status, and msg,
        as well as everything in self.loaded_attributes, and everything returned by self._extra_context().

        This means that input types that only parse attributes and pass them to the template get everything they need,
        and don't need to override this method.
        """
        context = {
            'id': self.input_id,
            'value': self.value,
            'status': Status(self.status, self.capa_system.i18n.ugettext),
            'msg': self.msg,
            'response_data': self.response_data,
            'STATIC_URL': self.capa_system.STATIC_URL,
            'describedby': '',
        }

        # Don't add aria-describedby attribute if there are no descriptions
        if self.response_data.get('descriptions'):
            description_ids = ' '.join(self.response_data.get('descriptions').keys())
            context.update(
                {'describedby': 'aria-describedby="{}"'.format(description_ids)}
            )

        context.update(
            (a, v) for (a, v) in self.loaded_attributes.iteritems() if a in self.to_render
        )
        context.update(self._extra_context())
        if self.answervariable:
            context.update({'answervariable': self.answervariable})
        return context

    def _extra_context(self):
        """
        Subclasses can override this to return extra context that should be passed to their templates for rendering.

        This is useful when the input type requires computing new template variables from the parsed attributes.
        """
        return {}

    def get_html(self):
        """
        Return the html for this input, as an etree element.
        """
        if self.template is None:
            raise NotImplementedError("no rendering template specified for class {0}"
                                      .format(self.__class__))

        context = self._get_render_context()

        html = self.capa_system.render_template(self.template, context)

        try:
            output = etree.XML(html)
        except etree.XMLSyntaxError as ex:
            # If `html` contains attrs with no values, like `controls` in <audio controls src='smth'/>,
            # XML parser will raise exception, so wee fallback to html5parser, which will set empty "" values for such attrs.
            try:
                output = html5lib.parseFragment(html, treebuilder='lxml', namespaceHTMLElements=False)[0]
            except IndexError:
                raise ex

        return output

    def get_user_visible_answer(self, internal_answer):
        """
        Given the internal representation of the answer provided by the user, return the representation of the answer
        as the user saw it.  Subclasses should override this method if and only if the internal represenation of the
        answer is different from the answer that is displayed to the user.
        """
        return internal_answer


#-----------------------------------------------------------------------------


@registry.register
class OptionInput(InputTypeBase):
    """
    Input type for selecting and Select option input type.

    Example:

    <optioninput options="('Up','Down')" correct="Up"/><text>The location of the sky</text>

    # TODO: allow ordering to be randomized
    """

    template = "optioninput.html"
    tags = ['optioninput']

    @staticmethod
    def parse_options(options):
        """
        Given options string, convert it into an ordered list of (option_id, option_description) tuples, where
        id==description for now.  TODO: make it possible to specify different id and descriptions.
        """
        # convert single quotes inside option values to html encoded string
        options = re.sub(r"([a-zA-Z])('|\\')([a-zA-Z])", r"\1&#39;\3", options)
        options = re.sub(r"\\'", r"&#39;", options)  # replace already escaped single quotes
        # parse the set of possible options
        lexer = shlex.shlex(options[1:-1].encode('utf8'))
        lexer.quotes = "'"
        # Allow options to be separated by whitespace as well as commas
        lexer.whitespace = ", "

        # remove quotes
        # convert escaped single quotes (html encoded string) back to single quotes
        tokens = [x[1:-1].decode('utf8').replace("&#39;", "'") for x in lexer]

        # make list of (option_id, option_description), with description=id
        return [(t, t) for t in tokens]

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [Attribute('options', transform=cls.parse_options),
                Attribute('inline', False)]

#-----------------------------------------------------------------------------


# TODO: consolidate choicegroup, radiogroup, checkboxgroup after discussion of
# desired semantics.

@registry.register
class ChoiceGroup(InputTypeBase):
    """
    Radio button or checkbox inputs: multiple choice or true/false

    TODO: allow order of choices to be randomized, following lon-capa spec.  Use
    "location" attribute, ie random, top, bottom.

    Example:

    <choicegroup>
      <choice correct="false" name="foil1">
        <text>This is foil One.</text>
      </choice>
      <choice correct="false" name="foil2">
        <text>This is foil Two.</text>
      </choice>
      <choice correct="true" name="foil3">
        <text>This is foil Three.</text>
      </choice>
    </choicegroup>
    """
    template = "choicegroup.html"
    tags = ['choicegroup', 'radiogroup', 'checkboxgroup']

    def setup(self):
        i18n = self.capa_system.i18n
        # suffix is '' or [] to change the way the input is handled in --as a scalar or vector
        # value.  (VS: would be nice to make this less hackish).
        if self.tag == 'choicegroup':
            self.suffix = ''
            self.html_input_type = "radio"
        elif self.tag == 'radiogroup':
            self.html_input_type = "radio"
            self.suffix = '[]'
        elif self.tag == 'checkboxgroup':
            self.html_input_type = "checkbox"
            self.suffix = '[]'
        else:
            _ = i18n.ugettext
            # Translators: 'ChoiceGroup' is an input type and should not be translated.
            msg = _("ChoiceGroup: unexpected tag {tag_name}").format(tag_name=self.tag)
            raise Exception(msg)

        self.choices = self.extract_choices(self.xml, i18n)
        self._choices_map = dict(self.choices,)

    @classmethod
    def get_attributes(cls):
        # Make '_' a no-op so we can scrape strings. Using lambda instead of
        #  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
        _ = lambda text: text
        return [Attribute("show_correctness", "always"),
                Attribute("submitted_message", _("Answer received."))]

    def _extra_context(self):
        return {'input_type': self.html_input_type,
                'choices': self.choices,
                'name_array_suffix': self.suffix}

    @staticmethod
    def extract_choices(element, i18n):
        """
        Extracts choices for a few input types, such as ChoiceGroup, RadioGroup and
        CheckboxGroup.

        returns list of (choice_name, choice_text) tuples

        TODO: allow order of choices to be randomized, following lon-capa spec.  Use
        "location" attribute, ie random, top, bottom.
        """

        choices = []
        _ = i18n.ugettext

        for choice in element:
            if choice.tag == 'choice':
                choices.append((choice.get("name"), stringify_children(choice)))
            else:
                if choice.tag != 'compoundhint':
                    msg = u'[capa.inputtypes.extract_choices] {error_message}'.format(
                        # Translators: '<choice>' and '<compoundhint>' are tag names and should not be translated.
                        error_message=_('Expected a <choice> or <compoundhint> tag; got {given_tag} instead').format(
                            given_tag=choice.tag
                        )
                    )
                    raise Exception(msg)
        return choices

    def get_user_visible_answer(self, internal_answer):
        if isinstance(internal_answer, basestring):
            return self._choices_map[internal_answer]

        return [self._choices_map[i] for i in internal_answer]


#-----------------------------------------------------------------------------


@registry.register
class JavascriptInput(InputTypeBase):
    """
    Hidden field for javascript to communicate via; also loads the required
    scripts for rendering the problem and passes data to the problem.

    TODO (arjun?): document this in detail.  Initial notes:
    - display_class is a subclass of XProblemClassDisplay (see
        xmodule/xmodule/js/src/capa/display.coffee),
    - display_file is the js script to be in /static/js/ where display_class is defined.
    """

    template = "javascriptinput.html"
    tags = ['javascriptinput']

    @classmethod
    def get_attributes(cls):
        """
        Register the attributes.
        """
        return [Attribute('params', None),
                Attribute('problem_state', None),
                Attribute('display_class', None),
                Attribute('display_file', None), ]

    def setup(self):
        # Need to provide a value that JSON can parse if there is no
        # student-supplied value yet.
        if self.value == "":
            self.value = 'null'


#-----------------------------------------------------------------------------


@registry.register
class JSInput(InputTypeBase):
    """
    Inputtype for general javascript inputs. Intended to be used with
    customresponse.
    Loads in a sandboxed iframe to help prevent css and js conflicts between
    frame and top-level window.

    iframe sandbox whitelist:
        - allow-scripts
        - allow-popups
        - allow-forms
        - allow-pointer-lock

    This in turn means that the iframe cannot directly access the top-level
    window elements.
      Example:

        <jsinput html_file="/static/test.html"
                 gradefn="grade"
                 height="500"
                 width="400"/>

    See the documentation in docs/data/source/course_data_formats/jsinput.rst
    for more information.
    """

    template = "jsinput.html"
    tags = ['jsinput']

    @classmethod
    def get_attributes(cls):
        """
        Register the attributes.
        """
        return [
            Attribute('params', None),       # extra iframe params
            Attribute('html_file', None),
            Attribute('gradefn', "gradefn"),
            Attribute('get_statefn', None),  # Function to call in iframe
                                             #   to get current state.
            Attribute('initial_state', None),  # JSON string to be used as initial state
            Attribute('set_statefn', None),  # Function to call iframe to
                                             #   set state
            Attribute('width', "400"),       # iframe width
            Attribute('height', "300"),      # iframe height
            Attribute('sop', None)           # SOP will be relaxed only if this
                                             # attribute is set to false.
        ]

    def _extra_context(self):
        context = {
            'jschannel_loader': '{static_url}js/capa/src/jschannel.js'.format(
                static_url=self.capa_system.STATIC_URL),
            'jsinput_loader': '{static_url}js/capa/src/jsinput.js'.format(
                static_url=self.capa_system.STATIC_URL),
            'saved_state': self.value
        }

        return context

#-----------------------------------------------------------------------------


@registry.register
class TextLine(InputTypeBase):
    """
    A text line input.  Can do math preview if "math"="1" is specified.

    If "trailing_text" is set to a value, then the textline will be shown with
    the value after the text input, and before the checkmark or any input-specific
    feedback. HTML will not work, but properly escaped HTML characters will. This
    feature is useful if you would like to specify a specific type of units for the
    text input.

    If the hidden attribute is specified, the textline is hidden and the input id
    is stored in a div with name equal to the value of the hidden attribute.  This
    is used e.g. for embedding simulations turned into questions.

    Example:
        <textline math="1" trailing_text="m/s"/>

    This example will render out a text line with a math preview and the text 'm/s'
    after the end of the text line.
    """

    template = "textline.html"
    tags = ['textline']

    @classmethod
    def get_attributes(cls):
        """
        Register the attributes.
        """
        return [
            Attribute('size', None),

            Attribute('hidden', False),
            Attribute('inline', False),

            # Attributes below used in setup(), not rendered directly.
            Attribute('math', None, render=False),
            # TODO: 'dojs' flag is temporary, for backwards compatibility with
            # 8.02x
            Attribute('dojs', None, render=False),
            Attribute('preprocessorClassName', None, render=False),
            Attribute('preprocessorSrc', None, render=False),
            Attribute('trailing_text', ''),
        ]

    def setup(self):
        self.do_math = bool(self.loaded_attributes['math'] or
                            self.loaded_attributes['dojs'])

        # TODO: do math checking using ajax instead of using js, so
        # that we only have one math parser.
        self.preprocessor = None
        if self.do_math:
            # Preprocessor to insert between raw input and Mathjax
            self.preprocessor = {
                'class_name': self.loaded_attributes['preprocessorClassName'],
                'script_src': self.loaded_attributes['preprocessorSrc'],
            }
            if None in self.preprocessor.values():
                self.preprocessor = None

    def _extra_context(self):
        return {'do_math': self.do_math,
                'preprocessor': self.preprocessor, }

#-----------------------------------------------------------------------------


@registry.register
class FileSubmission(InputTypeBase):
    """
    Upload some files (e.g. for programming assignments)
    """

    template = "filesubmission.html"
    tags = ['filesubmission']

    @staticmethod
    def parse_files(files):
        """
        Given a string like 'a.py b.py c.out', split on whitespace and return as a json list.
        """
        return json.dumps(files.split())

    @classmethod
    def get_attributes(cls):
        """
        Convert the list of allowed files to a convenient format.
        """
        return [Attribute('allowed_files', '[]', transform=cls.parse_files),
                Attribute('required_files', '[]', transform=cls.parse_files), ]

    def setup(self):
        """
        Do some magic to handle queueing status (render as "queued" instead of "incomplete"),
        pull queue_len from the msg field.  (TODO: get rid of the queue_len hack).
        """
        _ = self.capa_system.i18n.ugettext
        submitted_msg = _("Your files have been submitted. As soon as your submission is"
                          " graded, this message will be replaced with the grader's feedback.")
        self.submitted_msg = submitted_msg

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of
        # queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = self.submitted_msg

    def _extra_context(self):
        return {'queue_len': self.queue_len, }


#-----------------------------------------------------------------------------

@registry.register
class CodeInput(InputTypeBase):
    """
    A text area input for code--uses codemirror, does syntax highlighting, special tab handling,
    etc.
    """

    template = "codeinput.html"
    tags = [
        'codeinput',
        'textbox',
        # Another (older) name--at some point we may want to make it use a
        # non-codemirror editor.
    ]

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [
            Attribute('rows', '30'),
            Attribute('cols', '80'),
            Attribute('hidden', ''),

            # For CodeMirror
            Attribute('mode', 'python'),
            Attribute('linenumbers', 'true'),
            # Template expects tabsize to be an int it can do math with
            Attribute('tabsize', 4, transform=int),
        ]

    def setup_code_response_rendering(self):
        """
        Implement special logic: handle queueing state, and default input.
        """
        # if no student input yet, then use the default input given by the
        # problem
        if not self.value and self.xml.text:
            self.value = self.xml.text.strip()

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of
        # queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = bleach.clean(self.submitted_msg)

    def setup(self):
        """ setup this input type """
        _ = self.capa_system.i18n.ugettext
        submitted_msg = _("Your answer has been submitted. As soon as your submission is"
                          " graded, this message will be replaced with the grader's feedback.")
        self.submitted_msg = submitted_msg

        self.setup_code_response_rendering()

    def _extra_context(self):
        """Defined queue_len, add it """
        return {'queue_len': self.queue_len, }


#-----------------------------------------------------------------------------


@registry.register
class MatlabInput(CodeInput):
    """
    InputType for handling Matlab code input

    Example:
     <matlabinput rows="10" cols="80" tabsize="4">
        Initial Text
     </matlabinput>
    """
    template = "matlabinput.html"
    tags = ['matlabinput']

    def setup(self):
        """
        Handle matlab-specific parsing
        """
        _ = self.capa_system.i18n.ugettext

        submitted_msg = _("Submitted. As soon as a response is returned, "
                          "this message will be replaced by that feedback.")
        self.submitted_msg = submitted_msg

        self.setup_code_response_rendering()

        xml = self.xml

        self.plot_payload = xml.findtext('./plot_payload')
        # Check if problem has been queued
        self.queuename = 'matlab'
        self.queue_msg = ''
        # this is only set if we don't have a graded response
        # the graded response takes precedence
        if 'queue_msg' in self.input_state and self.status in ['queued', 'incomplete', 'unsubmitted']:
            self.queue_msg = sanitize_html(self.input_state['queue_msg'])

        if 'queuestate' in self.input_state and self.input_state['queuestate'] == 'queued':
            self.status = 'queued'
            self.queue_len = 1
            self.msg = self.submitted_msg
            # Handle situation if no response from xqueue arrived during specified time.
            if ('queuetime' not in self.input_state or
                    time.time() - self.input_state['queuetime'] > XQUEUE_TIMEOUT):
                self.queue_len = 0
                self.status = 'unsubmitted'
                self.msg = _(
                    'No response from Xqueue within {xqueue_timeout} seconds. Aborted.'
                ).format(xqueue_timeout=XQUEUE_TIMEOUT)

    def handle_ajax(self, dispatch, data):
        """
        Handle AJAX calls directed to this input

        Args:
            - dispatch (str) - indicates how we want this ajax call to be handled
            - data (dict) - dictionary of key-value pairs that contain useful data
        Returns:
            dict - 'success' - whether or not we successfully queued this submission
                 - 'message' - message to be rendered in case of error
        """

        if dispatch == 'plot':
            return self._plot_data(data)
        return {}

    def ungraded_response(self, queue_msg, queuekey):
        """
        Handle the response from the XQueue
        Stores the response in the input_state so it can be rendered later

        Args:
            - queue_msg (str) - message returned from the queue. The message to be rendered
            - queuekey (str) - a key passed to the queue. Will be matched up to verify that this is the response we're waiting for

        Returns:
            nothing
        """
        # check the queuekey against the saved queuekey
        if('queuestate' in self.input_state and self.input_state['queuestate'] == 'queued'
                and self.input_state['queuekey'] == queuekey):
            msg = self._parse_data(queue_msg)
            # save the queue message so that it can be rendered later
            self.input_state['queue_msg'] = msg
            self.input_state['queuestate'] = None
            self.input_state['queuekey'] = None

    def button_enabled(self):
        """ Return whether or not we want the 'Test Code' button visible

        Right now, we only want this button to show up when a problem has not been
        checked.
        """
        if self.status in ['correct', 'incorrect', 'partially-correct']:
            return False
        else:
            return True

    def _extra_context(self):
        """ Set up additional context variables"""

        _ = self.capa_system.i18n.ugettext

        queue_msg = self.queue_msg
        if len(self.queue_msg) > 0:  # An empty string cannot be parsed as XML but is okay to include in the template.
            try:
                etree.XML(u'<div>{0}</div>'.format(self.queue_msg))
            except etree.XMLSyntaxError:
                try:
                    html5lib.parseFragment(self.queue_msg, treebuilder='lxml', namespaceHTMLElements=False)[0]
                except (IndexError, ValueError):
                    # If neither can parse queue_msg, it contains invalid xml.
                    queue_msg = u"<span>{0}</span>".format(_("Error running code."))

        extra_context = {
            'queue_len': str(self.queue_len),
            'queue_msg': queue_msg,
            'button_enabled': self.button_enabled(),
            'matlab_editor_js': '{static_url}js/vendor/CodeMirror/octave.js'.format(
                static_url=self.capa_system.STATIC_URL),
            'msg': sanitize_html(self.msg)  # sanitize msg before rendering into template
        }
        return extra_context

    def _parse_data(self, queue_msg):
        """
        Parses the message out of the queue message
        Args:
            queue_msg (str) - a JSON encoded string
        Returns:
            returns the value for the the key 'msg' in queue_msg
        """
        try:
            result = json.loads(queue_msg)
        except (TypeError, ValueError):
            log.error("External message should be a JSON serialized dict."
                      " Received queue_msg = %s", queue_msg)
            raise
        msg = result['msg']
        return msg

    def _plot_data(self, data):
        """
        AJAX handler for the plot button
        Args:
            get (dict) - should have key 'submission' which contains the student submission
        Returns:
            dict - 'success' - whether or not we successfully queued this submission
                 - 'message' - message to be rendered in case of error
        """
        _ = self.capa_system.i18n.ugettext
        # only send data if xqueue exists
        if self.capa_system.xqueue is None:
            return {'success': False, 'message': _('Cannot connect to the queue')}

        # pull relevant info out of get
        response = data['submission']

        # construct xqueue headers
        qinterface = self.capa_system.xqueue['interface']
        qtime = datetime.utcnow().strftime(xqueue_interface.dateformat)
        callback_url = self.capa_system.xqueue['construct_callback']('ungraded_response')
        anonymous_student_id = self.capa_system.anonymous_student_id
        # TODO: Why is this using self.capa_system.seed when we have self.seed???
        queuekey = xqueue_interface.make_hashkey(str(self.capa_system.seed) + qtime +
                                                 anonymous_student_id +
                                                 self.input_id)
        xheader = xqueue_interface.make_xheader(
            lms_callback_url=callback_url,
            lms_key=queuekey,
            queue_name=self.queuename)

        # construct xqueue body
        student_info = {
            'anonymous_student_id': anonymous_student_id,
            'submission_time': qtime
        }
        contents = {
            'grader_payload': self.plot_payload,
            'student_info': json.dumps(student_info),
            'student_response': response,
            'token': getattr(self.capa_system, 'matlab_api_key', None),
            'endpoint_version': "2",
            'requestor_id': anonymous_student_id,
        }

        (error, msg) = qinterface.send_to_queue(header=xheader,
                                                body=json.dumps(contents))
        # save the input state if successful
        if error == 0:
            self.input_state['queuekey'] = queuekey
            self.input_state['queuestate'] = 'queued'
            self.input_state['queuetime'] = time.time()

        return {'success': error == 0, 'message': msg}


#-----------------------------------------------------------------------------

@registry.register
class Schematic(InputTypeBase):
    """
    InputType for the schematic editor
    """

    template = "schematicinput.html"
    tags = ['schematic']

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [
            Attribute('height', None),
            Attribute('width', None),
            Attribute('parts', None),
            Attribute('analyses', None),
            Attribute('initial_value', None),
            Attribute('submit_analyses', None),
        ]

    def _extra_context(self):
        context = {
            'setup_script': '{static_url}js/capa/schematicinput.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

        return context

#-----------------------------------------------------------------------------


@registry.register
class ImageInput(InputTypeBase):
    """
    Clickable image as an input field.  Element should specify the image source, height,
    and width, e.g.

    <imageinput src="/static/Figures/Skier-conservation-of-energy.jpg" width="388" height="560" />

    TODO: showanswer for imageimput does not work yet - need javascript to put rectangle
    over acceptable area of image.
    """

    template = "imageinput.html"
    tags = ['imageinput']

    @classmethod
    def get_attributes(cls):
        """
        Note: src, height, and width are all required.
        """
        return [Attribute('src'),
                Attribute('height'),
                Attribute('width'), ]

    def setup(self):
        """
        if value is of the form [x,y] then parse it and send along coordinates of previous answer
        """
        m = re.match(r'\[([0-9]+),([0-9]+)]',
                     self.value.strip().replace(' ', ''))
        if m:
            # Note: we subtract 15 to compensate for the size of the dot on the screen.
            # (is a 30x30 image--lms/static/images/green-pointer.png).
            (self.gx, self.gy) = [int(x) - 15 for x in m.groups()]
        else:
            (self.gx, self.gy) = (0, 0)

    def _extra_context(self):

        return {'gx': self.gx,
                'gy': self.gy}

#-----------------------------------------------------------------------------


@registry.register
class Crystallography(InputTypeBase):
    """
    An input for crystallography -- user selects 3 points on the axes, and we get a plane.

    TODO: what's the actual value format?
    """

    template = "crystallography.html"
    tags = ['crystallography']

    @classmethod
    def get_attributes(cls):
        """
        Note: height, width are required.
        """
        return [Attribute('height'),
                Attribute('width'),
                ]

# -------------------------------------------------------------------------


@registry.register
class VseprInput(InputTypeBase):
    """
    Input for molecular geometry--show possible structures, let student
    pick structure and label positions with atoms or electron pairs.
    """

    template = 'vsepr_input.html'
    tags = ['vsepr_input']

    @classmethod
    def get_attributes(cls):
        """
        Note: height, width, molecules and geometries are required.
        """
        return [Attribute('height'),
                Attribute('width'),
                Attribute('molecules'),
                Attribute('geometries'),
                ]

#-------------------------------------------------------------------------


@registry.register
class ChemicalEquationInput(InputTypeBase):
    """
    An input type for entering chemical equations.  Supports live preview.

    Example:

    <chemicalequationinput size="50"/>

    options: size -- width of the textbox.
    """

    template = "chemicalequationinput.html"
    tags = ['chemicalequationinput']

    @classmethod
    def get_attributes(cls):
        """
        Can set size of text field.
        """
        return [Attribute('size', '20'), ]

    def _extra_context(self):
        """
        TODO (vshnayder): Get rid of this once we have a standard way of requiring js to be loaded.
        """
        return {
            'previewer': '{static_url}js/capa/chemical_equation_preview.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

    def handle_ajax(self, dispatch, data):
        """
        Since we only have chemcalc preview this input, check to see if it
        matches the corresponding dispatch and send it through if it does
        """
        if dispatch == 'preview_chemcalc':
            return self.preview_chemcalc(data)
        return {}

    def preview_chemcalc(self, data):
        """
        Render an html preview of a chemical formula or equation.  get should
        contain a key 'formula' and value 'some formula string'.

        Returns a json dictionary:
        {
           'preview' : 'the-preview-html' or ''
           'error' : 'the-error' or ''
        }
        """

        _ = self.capa_system.i18n.ugettext
        result = {'preview': '',
                  'error': ''}
        try:
            formula = data['formula']
        except KeyError:
            result['error'] = _("No formula specified.")
            return result

        try:
            result['preview'] = chemcalc.render_to_html(formula)
        except pyparsing.ParseException as err:
            result['error'] = _("Couldn't parse formula: {error_msg}").format(error_msg=err.msg)
        except Exception:
            # this is unexpected, so log
            log.warning(
                "Error while previewing chemical formula", exc_info=True)
            result['error'] = _("Error while rendering preview")

        return result

#-------------------------------------------------------------------------


@registry.register
class FormulaEquationInput(InputTypeBase):
    """
    An input type for entering formula equations.  Supports live preview.

    Example:

    <formulaequationinput size="50"/>

    options: size -- width of the textbox.
             trailing_text -- text to show after the input textbox when
                              rendered, same as textline (useful for units)
    """

    template = "formulaequationinput.html"
    tags = ['formulaequationinput']

    @classmethod
    def get_attributes(cls):
        """
        Can set size of text field.
        """
        return [
            Attribute('size', '20'),
            Attribute('inline', False),
            Attribute('trailing_text', ''),
        ]

    def _extra_context(self):
        """
        TODO (vshnayder): Get rid of 'previewer' once we have a standard way of requiring js to be loaded.
        """
        # `reported_status` is basically `status`, except we say 'unanswered'

        return {
            'previewer': '{static_url}js/capa/src/formula_equation_preview.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

    def handle_ajax(self, dispatch, get):
        """
        Since we only have formcalc preview this input, check to see if it
        matches the corresponding dispatch and send it through if it does
        """
        if dispatch == 'preview_formcalc':
            return self.preview_formcalc(get)
        return {}

    def preview_formcalc(self, get):
        """
        Render an preview of a formula or equation. `get` should
        contain a key 'formula' with a math expression.

        Returns a json dictionary:
        {
           'preview' : '<some latex>' or ''
           'error' : 'the-error' or ''
           'request_start' : <time sent with request>
        }
        """
        _ = self.capa_system.i18n.ugettext
        result = {'preview': '',
                  'error': ''}

        try:
            formula = get['formula']
        except KeyError:
            result['error'] = _("No formula specified.")
            return result

        result['request_start'] = int(get.get('request_start', 0))

        try:
            # TODO add references to valid variables and functions
            # At some point, we might want to mark invalid variables as red
            # or something, and this is where we would need to pass those in.
            result['preview'] = latex_preview(formula)
        except pyparsing.ParseException:
            result['error'] = _("Sorry, couldn't parse formula")
            result['formula'] = formula
        except Exception:
            # this is unexpected, so log
            log.warning(
                "Error while previewing formula", exc_info=True
            )
            result['error'] = _("Error while rendering preview")

        return result

#-----------------------------------------------------------------------------


@registry.register
class DragAndDropInput(InputTypeBase):
    """
    Input for drag and drop problems. Allows student to drag and drop images and
    labels to base image.
    """

    template = 'drag_and_drop_input.html'
    tags = ['drag_and_drop_input']

    def setup(self):

        def parse(tag, tag_type):
            """Parses <tag ... /> xml element to dictionary. Stores
                'draggable' and 'target' tags with attributes to dictionary and
                returns last.

                Args:
                    tag: xml etree element <tag...> with attributes

                    tag_type: 'draggable' or 'target'.

                    If tag_type is 'draggable' : all attributes except id
                    (name or label or icon or can_reuse) are optional

                    If tag_type is 'target' all attributes (name, x, y, w, h)
                    are required. (x, y) - coordinates of center of target,
                    w, h - weight and height of target.

                Returns:
                    Dictionary of vaues of attributes:
                    dict{'name': smth, 'label': smth, 'icon': smth,
                    'can_reuse': smth}.
            """
            tag_attrs = dict()
            tag_attrs['draggable'] = {
                'id': Attribute._sentinel,
                'label': "", 'icon': "",
                'can_reuse': ""
            }

            tag_attrs['target'] = {
                'id': Attribute._sentinel,
                'x': Attribute._sentinel,
                'y': Attribute._sentinel,
                'w': Attribute._sentinel,
                'h': Attribute._sentinel
            }

            dic = dict()

            for attr_name in tag_attrs[tag_type].keys():
                dic[attr_name] = Attribute(attr_name,
                                           default=tag_attrs[tag_type][attr_name]).parse_from_xml(tag)

            if tag_type == 'draggable' and not self.no_labels:
                dic['label'] = dic['label'] or dic['id']

            if tag_type == 'draggable':
                dic['target_fields'] = [parse(target, 'target') for target in
                                        tag.iterchildren('target')]

            return dic

        # add labels to images?:
        self.no_labels = Attribute('no_labels',
                                   default="False").parse_from_xml(self.xml)

        to_js = dict()

        # image drag and drop onto
        to_js['base_image'] = Attribute('img').parse_from_xml(self.xml)

        # outline places on image where to drag adn drop
        to_js['target_outline'] = Attribute('target_outline',
                                            default="False").parse_from_xml(self.xml)
        # one draggable per target?
        to_js['one_per_target'] = Attribute('one_per_target',
                                            default="True").parse_from_xml(self.xml)
        # list of draggables
        to_js['draggables'] = [parse(draggable, 'draggable') for draggable in
                               self.xml.iterchildren('draggable')]
        # list of targets
        to_js['targets'] = [parse(target, 'target') for target in
                            self.xml.iterchildren('target')]

        # custom background color for labels:
        label_bg_color = Attribute('label_bg_color',
                                   default=None).parse_from_xml(self.xml)
        if label_bg_color:
            to_js['label_bg_color'] = label_bg_color

        self.loaded_attributes['drag_and_drop_json'] = json.dumps(to_js)
        self.to_render.add('drag_and_drop_json')

#-------------------------------------------------------------------------


@registry.register
class EditAMoleculeInput(InputTypeBase):
    """
    An input type for edit-a-molecule.  Integrates with the molecule editor java applet.

    Example:

    <editamolecule size="50"/>

    options: size -- width of the textbox.
    """

    template = "editamolecule.html"
    tags = ['editamoleculeinput']

    @classmethod
    def get_attributes(cls):
        """
        Can set size of text field.
        """
        return [Attribute('file'),
                Attribute('missing', None)]

    def _extra_context(self):
        context = {
            'applet_loader': '{static_url}js/capa/editamolecule.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

        return context

#-----------------------------------------------------------------------------


@registry.register
class DesignProtein2dInput(InputTypeBase):
    """
    An input type for design of a protein in 2D. Integrates with the Protex java applet.

    Example:

    <designprotein2d width="800" hight="500" target_shape="E;NE;NW;W;SW;E;none" />
    """

    template = "designprotein2dinput.html"
    tags = ['designprotein2dinput']

    @classmethod
    def get_attributes(cls):
        """
        Note: width, hight, and target_shape are required.
        """
        return [Attribute('width'),
                Attribute('height'),
                Attribute('target_shape')
                ]

    def _extra_context(self):
        context = {
            'applet_loader': '{static_url}js/capa/design-protein-2d.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

        return context

#-----------------------------------------------------------------------------


@registry.register
class EditAGeneInput(InputTypeBase):
    """
        An input type for editing a gene.
        Integrates with the genex GWT application.

        Example:

        <editagene genex_dna_sequence="CGAT" genex_problem_number="1"/>
    """

    template = "editageneinput.html"
    tags = ['editageneinput']

    @classmethod
    def get_attributes(cls):
        """
        Note: width, height, and dna_sequencee are required.
        """
        return [Attribute('genex_dna_sequence'),
                Attribute('genex_problem_number')
                ]

    def _extra_context(self):
        context = {
            'applet_loader': '{static_url}js/capa/edit-a-gene.js'.format(
                static_url=self.capa_system.STATIC_URL),
        }

        return context

#---------------------------------------------------------------------


@registry.register
class AnnotationInput(InputTypeBase):
    """
    Input type for annotations: students can enter some notes or other text
    (currently ungraded), and then choose from a set of tags/optoins, which are graded.

    Example:

        <annotationinput>
            <title>Annotation Exercise</title>
            <text>
                They are the ones who, at the public assembly, had put savage derangement [ate] into my thinking
                [phrenes] |89 on that day when I myself deprived Achilles of his honorific portion [geras]
            </text>
            <comment>Agamemnon says that ate or 'derangement' was the cause of his actions: why could Zeus say the same thing?</comment>
            <comment_prompt>Type a commentary below:</comment_prompt>
            <tag_prompt>Select one tag:</tag_prompt>
            <options>
                <option choice="correct">ate - both a cause and an effect</option>
                <option choice="incorrect">ate - a cause</option>
                <option choice="partially-correct">ate - an effect</option>
            </options>
        </annotationinput>

    # TODO: allow ordering to be randomized
    """

    template = "annotationinput.html"
    tags = ['annotationinput']

    def setup(self):
        xml = self.xml

        self.debug = False  # set to True to display extra debug info with input
        self.return_to_annotation = True  # return only works in conjunction with annotatable xmodule

        self.title = xml.findtext('./title', 'Annotation Exercise')
        self.text = xml.findtext('./text')
        self.comment = xml.findtext('./comment')
        self.comment_prompt = xml.findtext(
            './comment_prompt', 'Type a commentary below:')
        self.tag_prompt = xml.findtext('./tag_prompt', 'Select one tag:')
        self.options = self._find_options()

        # Need to provide a value that JSON can parse if there is no
        # student-supplied value yet.
        if self.value == '':
            self.value = 'null'

        self._validate_options()

    def _find_options(self):
        """ Returns an array of dicts where each dict represents an option. """
        elements = self.xml.findall('./options/option')
        return [{
                'id': index,
                'description': option.text,
                'choice': option.get('choice')
                } for (index, option) in enumerate(elements)]

    def _validate_options(self):
        """ Raises a ValueError if the choice attribute is missing or invalid. """
        valid_choices = ('correct', 'partially-correct', 'incorrect')
        for option in self.options:
            choice = option['choice']
            if choice is None:
                raise ValueError('Missing required choice attribute.')
            elif choice not in valid_choices:
                raise ValueError('Invalid choice attribute: {0}. Must be one of: {1}'.format(
                    choice, ', '.join(valid_choices)))

    def _unpack(self, json_value):
        """ Unpacks the json input state into a dict. """
        d = json.loads(json_value)
        if not isinstance(d, dict):
            d = {}

        comment_value = d.get('comment', '')
        if not isinstance(comment_value, basestring):
            comment_value = ''

        options_value = d.get('options', [])
        if not isinstance(options_value, list):
            options_value = []

        return {
            'options_value': options_value,
            'has_options_value': len(options_value) > 0,  # for convenience
            'comment_value': comment_value,
        }

    def _extra_context(self):
        extra_context = {
            'title': self.title,
            'text': self.text,
            'comment': self.comment,
            'comment_prompt': self.comment_prompt,
            'tag_prompt': self.tag_prompt,
            'options': self.options,
            'return_to_annotation': self.return_to_annotation,
            'debug': self.debug
        }

        extra_context.update(self._unpack(self.value))

        return extra_context


@registry.register
class ChoiceTextGroup(InputTypeBase):
    r"""
    Groups of radiobutton/checkboxes with text inputs.

    Examples:
    RadioButton problem
    <problem>
      <startouttext/>
        A person rolls a standard die 100 times and records the results.
        On the first roll they received a "1". Given this information
        select the correct choice and fill in numbers to make it accurate.
      <endouttext/>
      <choicetextresponse>
        <radiotextgroup>
          <choice correct="false">The lowest number rolled was:
            <decoy_input/> and the highest number rolled was:
            <decoy_input/> .</choice>
          <choice correct="true">The lowest number rolled was <numtolerance_input answer="1"/>
            and there is not enough information to determine the highest number rolled.
          </choice>
          <choice correct="false">There is not enough information to determine the lowest
          number rolled, and the highest number rolled was:
          <decoy_input/> .
          </choice>
        </radiotextgroup>
      </choicetextresponse>
    </problem>

    CheckboxProblem:
    <problem>
      <startouttext/>
        A person randomly selects 100 times, with replacement, from the list of numbers \(\sqrt{2}\) , 2, 3, 4 ,5 ,6
        and records the results. The first number they pick is \(\sqrt{2}\) Given this information
        select the correct choices and fill in numbers to make them accurate.
      <endouttext/>
      <choicetextresponse>
        <checkboxtextgroup>
             <choice correct="true">
                The lowest number selected was <numtolerance_input answer="1.4142" tolerance="0.01"/>
             </choice>
             <choice correct="false">
                The highest number selected was <decoy_input/> .
            </choice>
            <choice correct="true">There is not enough information given to determine the highest number
                which was selected.
            </choice>
            <choice correct="false">There is not enough information given to determine the lowest number
                selected.
            </choice>
        </checkboxtextgroup>
      </choicetextresponse>
    </problem>

    In the preceding examples the <decoy_input/> is used to generate a textinput html element
    in the problem's display. Since it is inside of an incorrect choice, no answer given
    for it will be correct, and thus specifying an answer for it is not needed.
    """
    template = "choicetext.html"
    tags = ['radiotextgroup', 'checkboxtextgroup']

    def setup(self):
        """
        Performs setup for the initial rendering of the problem.
        `self.html_input_type` determines whether this problem is displayed
        with radiobuttons or checkboxes

        If the initial value of `self.value` is '' change it to {} so that
        the template has an empty dictionary to work with.

        sets the value of self.choices to be equal to the return value of
        `self.extract_choices`
        """
        self.text_input_values = {}
        if self.tag == 'radiotextgroup':
            self.html_input_type = "radio"
        elif self.tag == 'checkboxtextgroup':
            self.html_input_type = "checkbox"
        else:
            _ = self.capa_system.i18n.ugettext
            msg = _("{input_type}: unexpected tag {tag_name}").format(
                input_type="ChoiceTextGroup", tag_name=self.tag
            )
            raise Exception(msg)

        if self.value == '':
            # Make `value` an empty dictionary, if it currently has an empty
            # value. This is necessary because the template expects a
            # dictionary.
            self.value = {}
        self.choices = self.extract_choices(self.xml, self.capa_system.i18n)

    @classmethod
    def get_attributes(cls):
        """
        Returns a list of `Attribute` for this problem type
        """
        # Make '_' a no-op so we can scrape strings. Using lambda instead of
        #  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
        _ = lambda text: text
        return [
            Attribute("show_correctness", "always"),
            Attribute("submitted_message", _("Answer received.")),
        ]

    def _extra_context(self):
        """
        Returns a dictionary of extra content necessary for rendering this InputType.

        `input_type` is either 'radio' or 'checkbox' indicating whether the choices for
        this problem will have radiobuttons or checkboxes.
        """
        return {
            'input_type': self.html_input_type,
            'choices': self.choices
        }

    @staticmethod
    def extract_choices(element, i18n):
        """
        Extracts choices from the xml for this problem type.
        If we have xml that is as follows(choice names will have been assigned
        by now)
        <radiotextgroup>
        <choice correct = "true" name ="1_2_1_choiceinput_0bc">
            The number
                <numtolerance_input name = "1_2_1_choiceinput0_numtolerance_input_0" answer="5"/>
            Is the mean of the list.
        </choice>
        <choice correct = "false" name = "1_2_1_choiceinput_1bc>
            False demonstration choice
        </choice>
        </radiotextgroup>

        Choices are used for rendering the problem properly
        The function will setup choices as follows:
        choices =[
            ("1_2_1_choiceinput_0bc",
                [{'type': 'text', 'contents': "The number", 'tail_text': '',
                  'value': ''
                  },
                  {'type': 'textinput',
                   'contents': "1_2_1_choiceinput0_numtolerance_input_0",
                   'tail_text': 'Is the mean of the list',
                   'value': ''
                   }
                ]
             ),
            ("1_2_1_choiceinput_1bc",
                [{'type': 'text', 'contents': "False demonstration choice",
                 'tail_text': '',
                  'value': ''
                  }
                ]
            )
        ]
        """

        _ = i18n.ugettext
        choices = []

        for choice in element:
            if choice.tag != 'choice':
                msg = u"[capa.inputtypes.extract_choices] {0}".format(
                    # Translators: a "tag" is an XML element, such as "<b>" in HTML
                    _("Expected a {expected_tag} tag; got {given_tag} instead").format(
                        expected_tag=u"<choice>",
                        given_tag=choice.tag,
                    )
                )
                raise Exception(msg)

            components = []
            choice_text = ''
            if choice.text is not None:
                choice_text += choice.text
            # Initialize our dict for the next content
            adder = {
                'type': 'text',
                'contents': choice_text,
                'tail_text': '',
                'value': ''
            }
            components.append(adder)

            for elt in choice:
                # for elements in the choice e.g. <text> <numtolerance_input>
                adder = {
                    'type': 'text',
                    'contents': '',
                    'tail_text': '',
                    'value': ''
                }
                tag_type = elt.tag
                # If the current `elt` is a <numtolerance_input> set the
                # `adder`type to 'numtolerance_input', and 'contents' to
                # the `elt`'s name.
                # Treat decoy_inputs and numtolerance_inputs the same in order
                # to prevent students from reading the Html and figuring out
                # which inputs are valid
                if tag_type in ('numtolerance_input', 'decoy_input'):
                    # We set this to textinput, so that we get a textinput html
                    # element.
                    adder['type'] = 'textinput'
                    adder['contents'] = elt.get('name')
                else:
                    adder['contents'] = elt.text

                # Add any tail text("is the mean" in the example)
                adder['tail_text'] = elt.tail if elt.tail else ''
                components.append(adder)

            # Add the tuple for the current choice to the list of choices
            choices.append((choice.get("name"), components))
        return choices
