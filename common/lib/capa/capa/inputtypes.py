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

These are matched by *.html files templates/*.html which are mako templates with the
actual html.

Each input type takes the xml tree as 'element', the previous answer as 'value', and the
graded status as'status'
"""

# TODO: rename "state" to "status" for all below.  status is currently the answer for the
# problem ID for the input element, but it will turn into a dict containing both the
# answer and any associated message for the problem ID for the input element.

import logging
import re
import shlex  # for splitting quoted strings
import json

from lxml import etree
import xml.sax.saxutils as saxutils
from registry import TagRegistry

log = logging.getLogger('mitx.' + __name__)

#########################################################################

registry = TagRegistry()

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

    def _get_render_context(self):
        """
        Abstract method.  Subclasses should implement to return the dictionary
        of keys needed to render their template.

        (Separate from get_html to faciliate testing of logic separately from the rendering)
        """
        raise NotImplementedError

    def get_html(self):
        """
        Return the html for this input, as an etree element.
        """
        if self.template is None:
            raise NotImplementedError("no rendering template specified for class {0}"
                                      .format(self.__class__))

        html = self.system.render_template(self.template, self._get_render_context())
        return etree.XML(html)


#-----------------------------------------------------------------------------


class OptionInput(InputTypeBase):
    """
    Input type for selecting and Select option input type.

    Example:

    <optioninput options="('Up','Down')" correct="Up"/><text>The location of the sky</text>
    """

    template = "optioninput.html"
    tags = ['optioninput']

    def __init__(self, system, xml, state):
        super(OptionInput, self).__init__(system, xml, state)

        # Extract the options...
        options = self.xml.get('options')
        if not options:
            raise Exception(
                "[courseware.capa.inputtypes.optioninput] Missing options specification in "
                + etree.tostring(self.xml))

        # parse the set of possible options
        oset = shlex.shlex(options[1:-1])
        oset.quotes = "'"
        oset.whitespace = ","
        oset = [x[1:-1] for x  in list(oset)]

        # make ordered list with (key, value) same
        self.osetdict = [(oset[x], oset[x]) for x in range(len(oset))]
        # TODO: allow ordering to be randomized

    def _get_render_context(self):

        context = {
            'id': self.id,
            'value': self.value,
            'state': self.status,
            'msg': self.msg,
            'options': self.osetdict,
            'inline': self.xml.get('inline',''),
            }
        return context

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

    def __init__(self, system, xml, state):
        super(ChoiceGroup, self).__init__(system, xml, state)

        if self.tag == 'choicegroup':
            self.suffix = ''
            if self.xml.get('type') == "MultipleChoice":
                self.element_type = "radio"
            elif self.xml.get('type') == "TrueFalse":
                # Huh?  Why TrueFalse->checkbox?  Each input can be true / false separately?
                self.element_type = "checkbox"
            else:
                self.element_type = "radio"

        elif self.tag == 'radiogroup':
            self.element_type = "radio"
            self.suffix = '[]'
        elif self.tag == 'checkboxgroup':
            self.element_type = "checkbox"
            self.suffix = '[]'
        else:
            raise Exception("ChoiceGroup: unexpected tag {0}".format(self.tag))

        self.choices = extract_choices(self.xml)

    def _get_render_context(self):
        context = {'id': self.id,
                   'value': self.value,
                   'state': self.status,
                   'input_type': self.element_type,
                   'choices': self.choices,
                   'name_array_suffix': self.suffix}
        return context

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
            raise Exception("[courseware.capa.inputtypes.extract_choices] \
                             Expected a <choice> tag; got %s instead"
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
    """

    template = "javascriptinput.html"
    tags = ['javascriptinput']

    def __init__(self, system, xml, state):
        super(JavascriptInput, self).__init__(system, xml, state)
        # Need to provide a value that JSON can parse if there is no
        # student-supplied value yet.
        if self.value == "":
            self.value = 'null'

        self.params = self.xml.get('params')
        self.problem_state = self.xml.get('problem_state')
        self.display_class = self.xml.get('display_class')
        self.display_file = self.xml.get('display_file')


    def _get_render_context(self):
        escapedict = {'"': '&quot;'}
        value = saxutils.escape(self.value, escapedict)
        msg   = saxutils.escape(self.msg, escapedict)

        context = {'id': self.id,
               'params': self.params,
               'display_file': self.display_file,
               'display_class': self.display_class,
               'problem_state': self.problem_state,
               'value': value,
               'evaluation': msg,
               }
        return context

registry.register(JavascriptInput)


#-----------------------------------------------------------------------------

class TextLine(InputTypeBase):
    """

    """

    template = "textinput.html"
    tags = ['textline']

    def __init__(self, system, xml, state):
        super(TextLine, self).__init__(system, xml, state)
        self.size = self.xml.get('size')

        # if specified, then textline is hidden and input id is stored
        # in div with name=self.hidden.
        self.hidden = self.xml.get('hidden', False)

        # TODO (vshnayder): can we get rid of inline?  Was it one of
        # the styling hacks early this semester?
        self.inline = self.xml.get('inline', False)

        # TODO: 'dojs' flag is temporary, for backwards compatibility with 8.02x
        self.do_math = bool(self.xml.get('math') or self.xml.get('dojs'))
        # TODO: do math checking using ajax instead of using js, so
        # that we only have one math parser.
        self.preprocessor = None
        if self.do_math:
            # Preprocessor to insert between raw input and Mathjax
            self.preprocessor = {'class_name': self.xml.get('preprocessorClassName',''),
                            'script_src': self.xml.get('preprocessorSrc','')}
            if '' in self.preprocessor.values():
                self.preprocessor = None



    def _get_render_context(self):
        # Escape answers with quotes, so they don't crash the system!
        escapedict = {'"': '&quot;'}
        value = saxutils.escape(self.value, escapedict)

        context = {'id': self.id,
                   'value': value,
                   'state': self.status,
                   'size': self.size,
                   'msg': self.msg,
                   'hidden': self.hidden,
                   'inline': self.inline,
                   'do_math': self.do_math,
                   'preprocessor': self.preprocessor,
               }
        return context

registry.register(TextLine)

#-----------------------------------------------------------------------------

class FileSubmission(InputTypeBase):
    """
    Upload some files (e.g. for programming assignments)
    """

    template = "filesubmission.html"
    tags = ['filesubmission']

    def __init__(self, system, xml, state):
        super(FileSubmission, self).__init__(system, xml, state)
        escapedict = {'"': '&quot;'}
        self.allowed_files  = json.dumps(xml.get('allowed_files', '').split())
        self.allowed_files  = saxutils.escape(self.allowed_files, escapedict)
        self.required_files = json.dumps(xml.get('required_files', '').split())
        self.required_files = saxutils.escape(self.required_files, escapedict)

        # Check if problem has been queued
        queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = 'Submitted to grader.'


    def _get_render_context(self):

        context = {'id': self.id,
                   'state': self.status,
                   'msg': self.msg,
                   'value': self.value,
                   'queue_len': self.queue_len,
                   'allowed_files': self.allowed_files,
                   'required_files': self.required_files,}
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
            'textbox',        # Old name for this.  Still supported, but deprecated.
            ]

    def __init__(self, system, xml, state):
        super(CodeInput, self).__init__(system, xml, state)

        self.rows = xml.get('rows') or '30'
        self.cols = xml.get('cols') or '80'
        # if specified, then textline is hidden and id is stored in div of name given by hidden
        self.hidden = xml.get('hidden', '')

        # if no student input yet, then use the default input given by the problem
        if not self.value:
            self.value = xml.text

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = 'Submitted to grader.'

        # For CodeMirror
        self.mode = xml.get('mode', 'python')
        self.linenumbers = xml.get('linenumbers', 'true')
        self.tabsize = int(xml.get('tabsize', '4'))

    def _get_render_context(self):

        context = {'id': self.id,
                   'value': self.value,
                   'state': self.status,
                   'msg': self.msg,
                   'mode': self.mode,
                   'linenumbers': self.linenumbers,
                   'rows': self.rows,
                   'cols': self.cols,
                   'hidden': self.hidden,
                   'tabsize': self.tabsize,
                   'queue_len': self.queue_len,
               }
        return context

registry.register(CodeInput)


#-----------------------------------------------------------------------------
class Schematic(InputTypeBase):
    """
    """

    template = "schematicinput.html"
    tags = ['schematic']

    def __init__(self, system, xml, state):
        super(Schematic, self).__init__(system, xml, state)
        self.height = xml.get('height')
        self.width = xml.get('width')
        self.parts = xml.get('parts')
        self.analyses = xml.get('analyses')
        self.initial_value = xml.get('initial_value')
        self.submit_analyses = xml.get('submit_analyses')


    def _get_render_context(self):

        context = {'id': self.id,
                   'value': self.value,
                   'initial_value': self.initial_value,
                   'state': self.status,
                   'width': self.width,
                   'height': self.height,
                   'parts': self.parts,
                   'analyses': self.analyses,
                   'submit_analyses': self.submit_analyses,               }
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

    def __init__(self, system, xml, state):
        super(ImageInput, self).__init__(system, xml, state)
        self.src = xml.get('src')
        self.height = xml.get('height')
        self.width = xml.get('width')

        # if value is of the form [x,y] then parse it and send along coordinates of previous answer
        m = re.match('\[([0-9]+),([0-9]+)]', self.value.strip().replace(' ', ''))
        if m:
            # TODO (vshnayder): why is there a "-15" here??
            (self.gx, self.gy) = [int(x) - 15 for x in m.groups()]
        else:
            (self.gx, self.gy) = (0, 0)


    def _get_render_context(self):

        context = {'id': self.id,
                   'value': self.value,
                   'height': self.height,
                   'width': self.width,
                   'src': self.src,
                   'gx': self.gx,
                   'gy': self.gy,
                   'state': self.status,    # to change (VS: to what??)
                   'msg': self.msg,         # to change
               }
        return context

registry.register(ImageInput)

#-----------------------------------------------------------------------------

class Crystallography(InputTypeBase):
    """
    An input for crystallography -- user selects 3 points on the axes, and we get a plane.

    TODO: what's the actual value format?
    """

    template = "crystallography.html"
    tags = ['crystallography']

    def __init__(self, system, xml, state):
        super(Crystallography, self).__init__(system, xml, state)

        self.height = xml.get('height')
        self.width = xml.get('width')
        self.size = xml.get('size')

        # if specified, then textline is hidden and id is stored in div of name given by hidden
        self.hidden = xml.get('hidden', '')

        # Escape answers with quotes, so they don't crash the system!
        escapedict = {'"': '&quot;'}
        self.value = saxutils.escape(self.value, escapedict)

    def _get_render_context(self):
        context = {'id': self.id,
                   'value': self.value,
                   'state': self.status,
                   'size': self.size,
                   'msg': self.msg,
                   'hidden': self.hidden,
                   'width': self.width,
                   'height': self.height,
               }
        return context

registry.register(Crystallography)

# -------------------------------------------------------------------------

class VseprInput(InputTypeBase):
    """
    Input for molecular geometry--show possible structures, let student
    pick structure and label positions with atoms or electron pairs.
    """

    template = 'vsepr_input.html'
    tags = ['vsepr_input']

    def __init__(self, system, xml, state):
        super(ImageInput, self).__init__(system, xml, state)

        self.height = xml.get('height')
        self.width = xml.get('width')

        # Escape answers with quotes, so they don't crash the system!
        escapedict = {'"': '&quot;'}
        self.value = saxutils.escape(self.value, escapedict)

        self.molecules = xml.get('molecules')
        self.geometries = xml.get('geometries')

    def _get_render_context(self):

        context = {'id': self.id,
                   'value': self.value,
                   'state': self.status,
                   'msg': self.msg,
                   'width': self.width,
                   'height': self.height,
                   'molecules': self.molecules,
                   'geometries': self.geometries,
               }
        return context

register_input_class(VseprInput)

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

    def _get_render_context(self):
        size = self.xml.get('size', '20')
        context = {
            'id': self.id,
            'value': self.value,
            'status': self.status,
            'size': size,
            'previewer': '/static/js/capa/chemical_equation_preview.js',
            }
        return context

registry.register(ChemicalEquationInput)
