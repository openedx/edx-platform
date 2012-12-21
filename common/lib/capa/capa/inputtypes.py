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

from collections import namedtuple
import json
import logging
from lxml import etree
import re
import shlex  # for splitting quoted strings
import sys

from registry import TagRegistry

log = logging.getLogger('mitx.' + __name__)

#########################################################################

registry = TagRegistry()

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
            raise ValueError('Missing required attribute {0}.'.format(self.name))

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

        - system    : ModuleSystem instance which provides OS, rendering, and user context.
                      Specifically, must have a render_template function.
        - xml       : Element tree of this Input element
        - state     : a dictionary with optional keys:
                      * 'value'  -- the current value of this input
                                    (what the student entered last time)
                      * 'id' -- the id of this input, typically
                                "{problem-location}_{response-num}_{input-num}"
                      * 'status' (answered, unanswered, unsubmitted)
                      * 'feedback' (dictionary containing keys for hints, errors, or other
                         feedback from previous attempt.  Specifically 'message', 'hint',
                         'hintmode'.  If 'hintmode' is 'always', the hint is always displayed.)
        """

        self.xml = xml
        self.tag = xml.tag
        self.system = system

        ## NOTE: ID should only come from one place.  If it comes from multiple,
        ## we use state first, XML second (in case the xml changed, but we have
        ## existing state with an old id). Since we don't make this guarantee,
        ## we can swap this around in the future if there's a more logical
        ## order.

        self.id = state.get('id', xml.get('id'))
        if self.id is None:
            raise ValueError("input id state is None. xml is {0}".format(etree.tostring(xml)))

        self.value = state.get('value', '')

        feedback = state.get('feedback', {})
        self.msg = feedback.get('message', '')
        self.hint = feedback.get('hint', '')
        self.hintmode = feedback.get('hintmode', None)

        # put hint above msg if it should be displayed
        if self.hintmode == 'always':
            self.msg = self.hint + ('<br/>' if self.msg else '') + self.msg

        self.status = state.get('status', 'unanswered')

        try:
            # Pre-parse and propcess all the declared requirements.
            self.process_requirements()

            # Call subclass "constructor" -- means they don't have to worry about calling
            # super().__init__, and are isolated from changes to the input constructor interface.
            self.setup()
        except Exception as err:
            # Something went wrong: add xml to message, but keep the traceback
            msg = "Error in xml '{x}': {err} ".format(x=etree.tostring(xml), err=str(err))
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
        # Use local dicts and sets so that if there are exceptions, we don't end up in a partially-initialized state.
        loaded = {}
        to_render = set()
        for a in self.get_attributes():
            loaded[a.name] = a.parse_from_xml(self.xml)
            if a.render:
                to_render.add(a.name)

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
            'id': self.id,
            'value': self.value,
            'status': self.status,
            'msg': self.msg,
            }
        context.update((a, v) for (a, v) in self.loaded_attributes.iteritems() if a in self.to_render)
        context.update(self._extra_context())
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

        html = self.system.render_template(self.template, context)
        return etree.XML(html)


#-----------------------------------------------------------------------------


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
        # parse the set of possible options
        lexer = shlex.shlex(options[1:-1])
        lexer.quotes = "'"
        # Allow options to be separated by whitespace as well as commas
        lexer.whitespace = ", "

        # remove quotes
        tokens = [x[1:-1] for x in list(lexer)]

        # make list of (option_id, option_description), with description=id
        return [(t, t) for t in tokens]

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [Attribute('options', transform=cls.parse_options),
                Attribute('inline', '')]

registry.register(OptionInput)

#-----------------------------------------------------------------------------


# TODO: consolidate choicegroup, radiogroup, checkboxgroup after discussion of
# desired semantics.

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
            raise Exception("ChoiceGroup: unexpected tag {0}".format(self.tag))

        self.choices = self.extract_choices(self.xml)

    def _extra_context(self):
        return {'input_type': self.html_input_type,
                'choices': self.choices,
                'name_array_suffix': self.suffix}

    @staticmethod
    def extract_choices(element):
        '''
        Extracts choices for a few input types, such as ChoiceGroup, RadioGroup and
        CheckboxGroup.

        returns list of (choice_name, choice_text) tuples

        TODO: allow order of choices to be randomized, following lon-capa spec.  Use
        "location" attribute, ie random, top, bottom.
        '''

        choices = []

        for choice in element:
            if choice.tag != 'choice':
                raise Exception(
                    "[capa.inputtypes.extract_choices] Expected a <choice> tag; got %s instead"
                    % choice.tag)
            choice_text = ''.join([etree.tostring(x) for x in choice])
            if choice.text is not None:
                # TODO: fix order?
                choice_text += choice.text

            choices.append((choice.get("name"), choice_text))

        return choices


registry.register(ChoiceGroup)


#-----------------------------------------------------------------------------


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
                Attribute('display_file', None),]


    def setup(self):
        # Need to provide a value that JSON can parse if there is no
        # student-supplied value yet.
        if self.value == "":
            self.value = 'null'

registry.register(JavascriptInput)


#-----------------------------------------------------------------------------

class TextLine(InputTypeBase):
    """
    A text line input.  Can do math preview if "math"="1" is specified.

    If the hidden attribute is specified, the textline is hidden and the input id is stored in a div with name equal
    to the value of the hidden attribute.  This is used e.g. for embedding simulations turned into questions.
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
            # TODO: 'dojs' flag is temporary, for backwards compatibility with 8.02x
            Attribute('dojs', None, render=False),
            Attribute('preprocessorClassName', None, render=False),
            Attribute('preprocessorSrc', None, render=False),
            ]


    def setup(self):
        self.do_math = bool(self.loaded_attributes['math'] or
                            self.loaded_attributes['dojs'])

        # TODO: do math checking using ajax instead of using js, so
        # that we only have one math parser.
        self.preprocessor = None
        if self.do_math:
            # Preprocessor to insert between raw input and Mathjax
            self.preprocessor = {'class_name': self.loaded_attributes['preprocessorClassName'],
                                 'script_src': self.loaded_attributes['preprocessorSrc']}
            if None in self.preprocessor.values():
                self.preprocessor = None


    def _extra_context(self):
        return {'do_math': self.do_math,
                'preprocessor': self.preprocessor,}

registry.register(TextLine)

#-----------------------------------------------------------------------------

class FileSubmission(InputTypeBase):
    """
    Upload some files (e.g. for programming assignments)
    """

    template = "filesubmission.html"
    tags = ['filesubmission']

    # pulled out for testing
    submitted_msg = ("Your file(s) have been submitted; as soon as your submission is"
                     " graded, this message will be replaced with the grader's feedback.")

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
                Attribute('required_files', '[]', transform=cls.parse_files),]

    def setup(self):
        """
        Do some magic to handle queueing status (render as "queued" instead of "incomplete"),
        pull queue_len from the msg field.  (TODO: get rid of the queue_len hack).
        """
        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = FileSubmission.submitted_msg

    def _extra_context(self):
        return {'queue_len': self.queue_len,}
        return context

registry.register(FileSubmission)


#-----------------------------------------------------------------------------

class CodeInput(InputTypeBase):
    """
    A text area input for code--uses codemirror, does syntax highlighting, special tab handling,
    etc.
    """

    template = "codeinput.html"
    tags = ['codeinput',
            'textbox',        # Another (older) name--at some point we may want to make it use a
                              # non-codemirror editor.
            ]

    # pulled out for testing
    submitted_msg = ("Submitted.  As soon as your submission is"
                     " graded, this message will be replaced with the grader's feedback.")

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [Attribute('rows', '30'),
                Attribute('cols', '80'),
                Attribute('hidden', ''),

                # For CodeMirror
                Attribute('mode', 'python'),
                Attribute('linenumbers', 'true'),
                # Template expects tabsize to be an int it can do math with
                Attribute('tabsize', 4, transform=int),
                ]

    def setup(self):
        """
        Implement special logic: handle queueing state, and default input.
        """
        # if no student input yet, then use the default input given by the problem
        if not self.value:
            self.value = self.xml.text

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = self.submitted_msg

    def _extra_context(self):
        """Defined queue_len, add it """
        return {'queue_len': self.queue_len,}

registry.register(CodeInput)


#-----------------------------------------------------------------------------
class Schematic(InputTypeBase):
    """
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
            Attribute('submit_analyses', None),]

        return context

registry.register(Schematic)

#-----------------------------------------------------------------------------

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
                Attribute('width'),]


    def setup(self):
        """
        if value is of the form [x,y] then parse it and send along coordinates of previous answer
        """
        m = re.match('\[([0-9]+),([0-9]+)]', self.value.strip().replace(' ', ''))
        if m:
            # Note: we subtract 15 to compensate for the size of the dot on the screen.
            # (is a 30x30 image--lms/static/green-pointer.png).
            (self.gx, self.gy) = [int(x) - 15 for x in m.groups()]
        else:
            (self.gx, self.gy) = (0, 0)


    def _extra_context(self):

        return {'gx': self.gx,
                'gy': self.gy}

registry.register(ImageInput)

#-----------------------------------------------------------------------------

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

registry.register(Crystallography)

# -------------------------------------------------------------------------


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

registry.register(VseprInput)

#--------------------------------------------------------------------------------


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
        return [Attribute('size', '20'),]

    def _extra_context(self):
        """
        TODO (vshnayder): Get rid of this once we have a standard way of requiring js to be loaded.
        """
        return {'previewer': '/static/js/capa/chemical_equation_preview.js',}

registry.register(ChemicalEquationInput)

#-----------------------------------------------------------------------------

class OpenEndedInput(InputTypeBase):
    """
    A text area input for code--uses codemirror, does syntax highlighting, special tab handling,
    etc.
    """

    template = "openendedinput.html"
    tags = ['openendedinput']

    # pulled out for testing
    submitted_msg = ("Feedback not yet available.  Reload to check again. "
                     "Once the problem is graded, this message will be "
                     "replaced with the grader's feedback")

    @classmethod
    def get_attributes(cls):
        """
        Convert options to a convenient format.
        """
        return [Attribute('rows', '30'),
                Attribute('cols', '80'),
                Attribute('hidden', ''),
                ]

    def setup(self):
        """
        Implement special logic: handle queueing state, and default input.
        """
        # if no student input yet, then use the default input given by the problem
        if not self.value:
            self.value = self.xml.text

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = self.submitted_msg

    def _extra_context(self):
        """Defined queue_len, add it """
        return {'queue_len': self.queue_len, }

registry.register(OpenEndedInput)

# -------------------------------------------------------------------------


class DragAndDropInput(InputTypeBase):
    """
    Input for molecular geometry--show possible structures, let student
    pick structure and label positions with atoms or electron pairs.
    """

    template = 'drag_and_drop_input.html'
    tags = ['drag_and_drop_input']

    @classmethod
    def get_attributes(cls):
        """
        Note: height, width, template and images are required.
        """
        return [Attribute('height'),
                Attribute('width'),
                Attribute('template'),
                Attribute('images'),
                ]

registry.register(DragAndDropInput)

#--------------------------------------------------------------------------------------------------------------------
