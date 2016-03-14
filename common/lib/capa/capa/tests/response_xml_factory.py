from lxml import etree
from abc import ABCMeta, abstractmethod


class ResponseXMLFactory(object):
    """ Abstract base class for capa response XML factories.
    Subclasses override create_response_element and
    create_input_element to produce XML of particular response types"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_response_element(self, **kwargs):
        """ Subclasses override to return an etree element
        representing the capa response XML
        (e.g. <numericalresponse>).

        The tree should NOT contain any input elements
        (such as <textline />) as these will be added later."""
        return None

    @abstractmethod
    def create_input_element(self, **kwargs):
        """ Subclasses override this to return an etree element
        representing the capa input XML (such as <textline />)"""
        return None

    def build_xml(self, **kwargs):
        """ Construct an XML string for a capa response
        based on **kwargs.

        **kwargs is a dictionary that will be passed
        to create_response_element() and create_input_element().
        See the subclasses below for other keyword arguments
        you can specify.

        For all response types, **kwargs can contain:

        *question_text*: The text of the question to display,
            wrapped in <p> tags.

        *explanation_text*: The detailed explanation that will
            be shown if the user answers incorrectly.

        *script*: The embedded Python script (a string)

        *num_responses*: The number of responses to create [DEFAULT: 1]

        *num_inputs*: The number of input elements
            to create [DEFAULT: 1]

        *credit_type*: String of comma-separated words specifying the
            partial credit grading scheme.

        Returns a string representation of the XML tree.
        """

        # Retrieve keyward arguments
        question_text = kwargs.get('question_text', '')
        explanation_text = kwargs.get('explanation_text', '')
        script = kwargs.get('script', None)
        num_responses = kwargs.get('num_responses', 1)
        num_inputs = kwargs.get('num_inputs', 1)
        credit_type = kwargs.get('credit_type', None)

        # The root is <problem>
        root = etree.Element("problem")

        # Add a script if there is one
        if script:
            script_element = etree.SubElement(root, "script")
            script_element.set("type", "loncapa/python")
            script_element.text = str(script)

        # The problem has a child <p> with question text
        question = etree.SubElement(root, "p")
        question.text = question_text

        # Add the response(s)
        for __ in range(int(num_responses)):
            response_element = self.create_response_element(**kwargs)

            # Set partial credit
            if credit_type is not None:
                response_element.set('partial_credit', str(credit_type))

            root.append(response_element)

            # Add input elements
            for __ in range(int(num_inputs)):
                input_element = self.create_input_element(**kwargs)
                if not None == input_element:
                    response_element.append(input_element)

            # The problem has an explanation of the solution
            if explanation_text:
                explanation = etree.SubElement(root, "solution")
                explanation_div = etree.SubElement(explanation, "div")
                explanation_div.set("class", "detailed-solution")
                explanation_div.text = explanation_text

        return etree.tostring(root)

    @staticmethod
    def textline_input_xml(**kwargs):
        """ Create a <textline/> XML element

        Uses **kwargs:

        *math_display*: If True, then includes a MathJax display of user input

        *size*: An integer representing the width of the text line
        """
        math_display = kwargs.get('math_display', False)
        size = kwargs.get('size', None)

        input_element = etree.Element('textline')

        if math_display:
            input_element.set('math', '1')

        if size:
            input_element.set('size', str(size))

        return input_element

    @staticmethod
    def choicegroup_input_xml(**kwargs):
        """ Create a <choicegroup> XML element

        Uses **kwargs:

        *choice_type*: Can be "checkbox", "radio", or "multiple"

        *choices*: List of True/False values indicating whether
                            a particular choice is correct or not.
                            Users must choose *all* correct options in order
                            to be marked correct.
                            DEFAULT: [True]

        *choice_names": List of strings identifying the choices.
                        If specified, you must ensure that
                        len(choice_names) == len(choices)

        *points*: List of strings giving partial credit values (0-1)
                  for each choice. Interpreted as floats in problem.
                  If specified, ensure len(points) == len(choices)
        """
        # Names of group elements
        group_element_names = {
            'checkbox': 'checkboxgroup',
            'radio': 'radiogroup',
            'multiple': 'choicegroup'
        }

        # Retrieve **kwargs
        choices = kwargs.get('choices', [True])
        choice_type = kwargs.get('choice_type', 'multiple')
        choice_names = kwargs.get('choice_names', [None] * len(choices))
        points = kwargs.get('points', [None] * len(choices))

        # Create the <choicegroup>, <checkboxgroup>, or <radiogroup> element
        assert choice_type in group_element_names
        group_element = etree.Element(group_element_names[choice_type])

        # Create the <choice> elements
        for (correct_val, name, pointval) in zip(choices, choice_names, points):
            choice_element = etree.SubElement(group_element, "choice")
            if correct_val is True:
                correctness = 'true'
            elif correct_val is False:
                correctness = 'false'
            elif 'partial' in correct_val:
                correctness = 'partial'

            choice_element.set('correct', correctness)

            # Add a name identifying the choice, if one exists
            # For simplicity, we use the same string as both the
            # name attribute and the text of the element
            if name:
                choice_element.text = str(name)
                choice_element.set("name", str(name))

            # Add point values for partially-correct choices.
            if pointval:
                choice_element.set("point_value", str(pointval))

        return group_element


class NumericalResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <numericalresponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create a <numericalresponse> XML element.
        Uses **kwarg keys:

        *answer*: The correct answer (e.g. "5")

        *tolerance*: The tolerance within which a response
        is considered correct.  Can be a decimal (e.g. "0.01")
        or percentage (e.g. "2%")

        *credit_type*: String of comma-separated words specifying the
        partial credit grading scheme.

        *partial_range*: The multiplier for the tolerance that will
        still provide partial credit in the "close" grading style

        *partial_answers*: A string of comma-separated alternate
        answers that will receive partial credit in the "list" style
        """

        answer = kwargs.get('answer', None)
        tolerance = kwargs.get('tolerance', None)
        credit_type = kwargs.get('credit_type', None)
        partial_range = kwargs.get('partial_range', None)
        partial_answers = kwargs.get('partial_answers', None)

        response_element = etree.Element('numericalresponse')

        if answer:
            if isinstance(answer, float):
                response_element.set('answer', repr(answer))
            else:
                response_element.set('answer', str(answer))

        if tolerance:
            responseparam_element = etree.SubElement(response_element, 'responseparam')
            responseparam_element.set('type', 'tolerance')
            responseparam_element.set('default', str(tolerance))
            if partial_range is not None and 'close' in credit_type:
                responseparam_element.set('partial_range', str(partial_range))

        if partial_answers is not None and 'list' in credit_type:
            # The line below throws a false positive pylint violation, so it's excepted.
            responseparam_element = etree.SubElement(response_element, 'responseparam')
            responseparam_element.set('partial_answers', partial_answers)

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)


class CustomResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <customresponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create a <customresponse> XML element.

        Uses **kwargs:

        *cfn*: the Python code to run.  Can be inline code,
        or the name of a function defined in earlier <script> tags.

        Should have the form: cfn(expect, answer_given, student_answers)
        where expect is a value (see below),
        answer_given is a single value (for 1 input)
        or a list of values (for multiple inputs),
        and student_answers is a dict of answers by input ID.

        *expect*: The value passed to the function cfn

        *answer*: Inline script that calculates the answer
        """

        # Retrieve **kwargs
        cfn = kwargs.get('cfn', None)
        expect = kwargs.get('expect', None)
        answer = kwargs.get('answer', None)
        options = kwargs.get('options', None)
        cfn_extra_args = kwargs.get('cfn_extra_args', None)

        # Create the response element
        response_element = etree.Element("customresponse")

        if cfn:
            response_element.set('cfn', str(cfn))

        if expect:
            response_element.set('expect', str(expect))

        if answer:
            answer_element = etree.SubElement(response_element, "answer")
            answer_element.text = str(answer)

        if options:
            response_element.set('options', str(options))

        if cfn_extra_args:
            response_element.set('cfn_extra_args', str(cfn_extra_args))

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)


class SchematicResponseXMLFactory(ResponseXMLFactory):
    """ Factory for creating <schematicresponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create the <schematicresponse> XML element.

        Uses *kwargs*:

        *answer*: The Python script used to evaluate the answer.
        """
        answer_script = kwargs.get('answer', None)

        # Create the <schematicresponse> element
        response_element = etree.Element("schematicresponse")

        # Insert the <answer> script if one is provided
        if answer_script:
            answer_element = etree.SubElement(response_element, "answer")
            answer_element.set("type", "loncapa/python")
            answer_element.text = str(answer_script)

        return response_element

    def create_input_element(self, **kwargs):
        """ Create the <schematic> XML element.

        Although <schematic> can have several attributes,
        (*height*, *width*, *parts*, *analyses*, *submit_analysis*, and *initial_value*),
        none of them are used in the capa module.
        For testing, we create a bare-bones version of <schematic>."""
        return etree.Element("schematic")


class CodeResponseXMLFactory(ResponseXMLFactory):
    """ Factory for creating <coderesponse> XML trees """

    def build_xml(self, **kwargs):
        # Since we are providing an <answer> tag,
        # we should override the default behavior
        # of including a <solution> tag as well
        kwargs['explanation_text'] = None
        return super(CodeResponseXMLFactory, self).build_xml(**kwargs)

    def create_response_element(self, **kwargs):
        """
        Create a <coderesponse> XML element.

        Uses **kwargs:

        *initial_display*: The code that initially appears in the textbox
                            [DEFAULT: "Enter code here"]
        *answer_display*: The answer to display to the student
                            [DEFAULT: "This is the correct answer!"]
        *grader_payload*: A JSON-encoded string sent to the grader
                            [DEFAULT: empty dict string]
        *allowed_files*: A space-separated string of file names.
                            [DEFAULT: None]
        *required_files*: A space-separated string of file names.
                            [DEFAULT: None]

        """
        # Get **kwargs
        initial_display = kwargs.get("initial_display", "Enter code here")
        answer_display = kwargs.get("answer_display", "This is the correct answer!")
        grader_payload = kwargs.get("grader_payload", '{}')
        allowed_files = kwargs.get("allowed_files", None)
        required_files = kwargs.get("required_files", None)

        # Create the <coderesponse> element
        response_element = etree.Element("coderesponse")

        # If files are involved, create the <filesubmission> element.
        has_files = allowed_files or required_files
        if has_files:
            filesubmission_element = etree.SubElement(response_element, "filesubmission")
            if allowed_files:
                filesubmission_element.set("allowed_files", allowed_files)
            if required_files:
                filesubmission_element.set("required_files", required_files)

        # Create the <codeparam> element.
        codeparam_element = etree.SubElement(response_element, "codeparam")

        # Set the initial display text
        initial_element = etree.SubElement(codeparam_element, "initial_display")
        initial_element.text = str(initial_display)

        # Set the answer display text
        answer_element = etree.SubElement(codeparam_element, "answer_display")
        answer_element.text = str(answer_display)

        # Set the grader payload string
        grader_element = etree.SubElement(codeparam_element, "grader_payload")
        grader_element.text = str(grader_payload)

        # Create the input within the response
        if not has_files:
            input_element = etree.SubElement(response_element, "textbox")
            input_element.set("mode", "python")

        return response_element

    def create_input_element(self, **kwargs):
        # Since we create this in create_response_element(),
        # return None here
        return None


class ChoiceResponseXMLFactory(ResponseXMLFactory):
    """ Factory for creating <choiceresponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create a <choiceresponse> element """
        return etree.Element("choiceresponse")

    def create_input_element(self, **kwargs):
        """ Create a <checkboxgroup> element."""
        return ResponseXMLFactory.choicegroup_input_xml(**kwargs)


class FormulaResponseXMLFactory(ResponseXMLFactory):
    """ Factory for creating <formularesponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create a <formularesponse> element.

        *sample_dict*: A dictionary of the form:
                        { VARIABLE_NAME: (MIN, MAX), ....}

                        This specifies the range within which
                        to numerically sample each variable to check
                        student answers.
                        [REQUIRED]

        *num_samples*: The number of times to sample the student's answer
                        to numerically compare it to the correct answer.

        *tolerance*: The tolerance within which answers will be accepted
                        [DEFAULT: 0.01]

        *answer*: The answer to the problem.  Can be a formula string
                    or a Python variable defined in a script
                    (e.g. "$calculated_answer" for a Python variable
                    called calculated_answer)
                    [REQUIRED]

        *hints*: List of (hint_prompt, hint_name, hint_text) tuples
                Where *hint_prompt* is the formula for which we show the hint,
                *hint_name* is an internal identifier for the hint,
                and *hint_text* is the text we show for the hint.
        """
        # Retrieve kwargs
        sample_dict = kwargs.get("sample_dict", None)
        num_samples = kwargs.get("num_samples", None)
        tolerance = kwargs.get("tolerance", 0.01)
        answer = kwargs.get("answer", None)
        hint_list = kwargs.get("hints", None)

        assert answer
        assert sample_dict and num_samples

        # Create the <formularesponse> element
        response_element = etree.Element("formularesponse")

        # Set the sample information
        sample_str = self._sample_str(sample_dict, num_samples, tolerance)
        response_element.set("samples", sample_str)

        # Set the tolerance
        responseparam_element = etree.SubElement(response_element, "responseparam")
        responseparam_element.set("type", "tolerance")
        responseparam_element.set("default", str(tolerance))

        # Set the answer
        response_element.set("answer", str(answer))

        # Include hints, if specified
        if hint_list:
            hintgroup_element = etree.SubElement(response_element, "hintgroup")

            for (hint_prompt, hint_name, hint_text) in hint_list:

                # For each hint, create a <formulahint> element
                formulahint_element = etree.SubElement(hintgroup_element, "formulahint")

                # We could sample a different range, but for simplicity,
                # we use the same sample string for the hints
                # that we used previously.
                formulahint_element.set("samples", sample_str)

                formulahint_element.set("answer", str(hint_prompt))
                formulahint_element.set("name", str(hint_name))

                # For each hint, create a <hintpart> element
                # corresponding to the <formulahint>
                hintpart_element = etree.SubElement(hintgroup_element, "hintpart")
                hintpart_element.set("on", str(hint_name))
                text_element = etree.SubElement(hintpart_element, "text")
                text_element.text = str(hint_text)

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)

    def _sample_str(self, sample_dict, num_samples, tolerance):
        # Loncapa uses a special format for sample strings:
        # "x,y,z@4,5,3:10,12,8#4" means plug in values for (x,y,z)
        # from within the box defined by points (4,5,3) and (10,12,8)
        # The "#4" means to repeat 4 times.
        variables = [str(v) for v in sample_dict.keys()]
        low_range_vals = [str(f[0]) for f in sample_dict.values()]
        high_range_vals = [str(f[1]) for f in sample_dict.values()]
        sample_str = (
            ",".join(sample_dict.keys()) + "@" +
            ",".join(low_range_vals) + ":" +
            ",".join(high_range_vals) +
            "#" + str(num_samples)
        )
        return sample_str


class ImageResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <imageresponse> XML """

    def create_response_element(self, **kwargs):
        """ Create the <imageresponse> element."""
        return etree.Element("imageresponse")

    def create_input_element(self, **kwargs):
        """ Create the <imageinput> element.

        Uses **kwargs:

        *src*: URL for the image file [DEFAULT: "/static/image.jpg"]

        *width*: Width of the image [DEFAULT: 100]

        *height*: Height of the image [DEFAULT: 100]

        *rectangle*: String representing the rectangles the user should select.

                    Take the form "(x1,y1)-(x2,y2)", where the two (x,y)
                    tuples define the corners of the rectangle.

                    Can include multiple rectangles separated by a semicolon, e.g.
                    "(490,11)-(556,98);(242,202)-(296,276)"

        *regions*: String representing the regions a user can select

                    Take the form "[ [[x1,y1], [x2,y2], [x3,y3]],
                                    [[x1,y1], [x2,y2], [x3,y3]] ]"
                    (Defines two regions, each with 3 points)

        REQUIRED: Either *rectangle* or *region* (or both)
        """

        # Get the **kwargs
        src = kwargs.get("src", "/static/image.jpg")
        width = kwargs.get("width", 100)
        height = kwargs.get("height", 100)
        rectangle = kwargs.get('rectangle', None)
        regions = kwargs.get('regions', None)

        assert rectangle or regions

        # Create the <imageinput> element
        input_element = etree.Element("imageinput")
        input_element.set("src", str(src))
        input_element.set("width", str(width))
        input_element.set("height", str(height))

        if rectangle:
            input_element.set("rectangle", rectangle)

        if regions:
            input_element.set("regions", regions)

        return input_element


class JavascriptResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <javascriptresponse> XML """

    def create_response_element(self, **kwargs):
        """ Create the <javascriptresponse> element.

        Uses **kwargs:

        *generator_src*: Name of the JS file to generate the problem.
        *grader_src*: Name of the JS file to grade the problem.
        *display_class*: Name of the class used to display the problem
        *display_src*: Name of the JS file used to display the problem
        *param_dict*: Dictionary of parameters to pass to the JS
        """
        # Get **kwargs
        generator_src = kwargs.get("generator_src", None)
        grader_src = kwargs.get("grader_src", None)
        display_class = kwargs.get("display_class", None)
        display_src = kwargs.get("display_src", None)
        param_dict = kwargs.get("param_dict", {})

        # Both display_src and display_class given,
        # or neither given
        assert((display_src and display_class) or
               (not display_src and not display_class))

        # Create the <javascriptresponse> element
        response_element = etree.Element("javascriptresponse")

        if generator_src:
            generator_element = etree.SubElement(response_element, "generator")
            generator_element.set("src", str(generator_src))

        if grader_src:
            grader_element = etree.SubElement(response_element, "grader")
            grader_element.set("src", str(grader_src))

        if display_class and display_src:
            display_element = etree.SubElement(response_element, "display")
            display_element.set("class", str(display_class))
            display_element.set("src", str(display_src))

        for (param_name, param_val) in param_dict.items():
            responseparam_element = etree.SubElement(response_element, "responseparam")
            responseparam_element.set("name", str(param_name))
            responseparam_element.set("value", str(param_val))

        return response_element

    def create_input_element(self, **kwargs):
        """ Create the <javascriptinput> element """
        return etree.Element("javascriptinput")


class MultipleChoiceResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <multiplechoiceresponse> XML """

    def create_response_element(self, **kwargs):
        """ Create the <multiplechoiceresponse> element"""
        return etree.Element('multiplechoiceresponse')

    def create_input_element(self, **kwargs):
        """ Create the <choicegroup> element"""
        kwargs['choice_type'] = 'multiple'
        return ResponseXMLFactory.choicegroup_input_xml(**kwargs)


class TrueFalseResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <truefalseresponse> XML """

    def create_response_element(self, **kwargs):
        """ Create the <truefalseresponse> element"""
        return etree.Element('truefalseresponse')

    def create_input_element(self, **kwargs):
        """ Create the <choicegroup> element"""
        kwargs['choice_type'] = 'multiple'
        return ResponseXMLFactory.choicegroup_input_xml(**kwargs)


class OptionResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <optionresponse> XML"""

    def create_response_element(self, **kwargs):
        """ Create the <optionresponse> element"""
        return etree.Element("optionresponse")

    def create_input_element(self, **kwargs):
        """ Create the <optioninput> element.

        Uses **kwargs:

        *options*: a list of possible options the user can choose from [REQUIRED]
                    You must specify at least 2 options.
        *correct_option*: the correct choice from the list of options [REQUIRED]
        """

        options_list = kwargs.get('options', None)
        correct_option = kwargs.get('correct_option', None)

        assert options_list and correct_option
        assert len(options_list) > 1
        assert correct_option in options_list

        # Create the <optioninput> element
        optioninput_element = etree.Element("optioninput")

        # Set the "options" attribute
        # Format: "('first', 'second', 'third')"
        options_attr_string = u",".join([u"'{}'".format(o) for o in options_list])
        options_attr_string = u"({})".format(options_attr_string)
        optioninput_element.set('options', options_attr_string)

        # Set the "correct" attribute
        optioninput_element.set('correct', str(correct_option))

        return optioninput_element


class StringResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <stringresponse> XML """

    def create_response_element(self, **kwargs):
        """ Create a <stringresponse> XML element.

            Uses **kwargs:

            *answer*: The correct answer (a string) [REQUIRED]

            *case_sensitive*: Whether the response is case-sensitive (True/False)
                            [DEFAULT: True]

            *hints*: List of (hint_prompt, hint_name, hint_text) tuples
                Where *hint_prompt* is the string for which we show the hint,
                *hint_name* is an internal identifier for the hint,
                and *hint_text* is the text we show for the hint.

            *hintfn*: The name of a function in the script to use for hints.

            *regexp*: Whether the response is regexp

            *additional_answers*: list of additional asnwers.

            *non_attribute_answers*: list of additional answers to be coded in the
                non-attribute format

        """
        # Retrieve the **kwargs
        answer = kwargs.get("answer", None)
        case_sensitive = kwargs.get("case_sensitive", None)
        hint_list = kwargs.get('hints', None)
        hint_fn = kwargs.get('hintfn', None)
        regexp = kwargs.get('regexp', None)
        additional_answers = kwargs.get('additional_answers', [])
        non_attribute_answers = kwargs.get('non_attribute_answers', [])
        assert answer

        # Create the <stringresponse> element
        response_element = etree.Element("stringresponse")

        # Set the answer attribute
        response_element.set("answer", unicode(answer))

        # Set the case sensitivity and regexp:
        type_value = ''
        if case_sensitive is not None:
            type_value += "cs" if case_sensitive else "ci"
        type_value += ' regexp' if regexp else ''
        if type_value:
            response_element.set("type", type_value.strip())

        # Add the hints if specified
        if hint_list or hint_fn:
            hintgroup_element = etree.SubElement(response_element, "hintgroup")
            if hint_list:
                assert not hint_fn
                for (hint_prompt, hint_name, hint_text) in hint_list:
                    stringhint_element = etree.SubElement(hintgroup_element, "stringhint")
                    stringhint_element.set("answer", str(hint_prompt))
                    stringhint_element.set("name", str(hint_name))

                    hintpart_element = etree.SubElement(hintgroup_element, "hintpart")
                    hintpart_element.set("on", str(hint_name))

                    hint_text_element = etree.SubElement(hintpart_element, "text")
                    hint_text_element.text = str(hint_text)

            if hint_fn:
                assert not hint_list
                hintgroup_element.set("hintfn", hint_fn)

        for additional_answer in additional_answers:
            additional_node = etree.SubElement(response_element, "additional_answer")
            additional_node.set("answer", additional_answer)

        for answer in non_attribute_answers:
            additional_node = etree.SubElement(response_element, "additional_answer")
            additional_node.text = answer

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)


class AnnotationResponseXMLFactory(ResponseXMLFactory):
    """ Factory for creating <annotationresponse> XML trees """
    def create_response_element(self, **kwargs):
        """ Create a <annotationresponse> element """
        return etree.Element("annotationresponse")

    def create_input_element(self, **kwargs):
        """ Create a <annotationinput> element."""

        input_element = etree.Element("annotationinput")

        text_children = [
            {'tag': 'title', 'text': kwargs.get('title', 'super cool annotation')},
            {'tag': 'text', 'text': kwargs.get('text', 'texty text')},
            {'tag': 'comment', 'text': kwargs.get('comment', 'blah blah erudite comment blah blah')},
            {'tag': 'comment_prompt', 'text': kwargs.get('comment_prompt', 'type a commentary below')},
            {'tag': 'tag_prompt', 'text': kwargs.get('tag_prompt', 'select one tag')}
        ]

        for child in text_children:
            etree.SubElement(input_element, child['tag']).text = child['text']

        default_options = [('green', 'correct'), ('eggs', 'incorrect'), ('ham', 'partially-correct')]
        options = kwargs.get('options', default_options)
        options_element = etree.SubElement(input_element, 'options')

        for (description, correctness) in options:
            option_element = etree.SubElement(options_element, 'option', {'choice': correctness})
            option_element.text = description

        return input_element


class SymbolicResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <symbolicresponse> xml """

    def create_response_element(self, **kwargs):
        """ Build the <symbolicresponse> XML element.

        Uses **kwargs:

        *expect*: The correct answer (a sympy string)

        *options*: list of option strings to pass to symmath_check
            (e.g. 'matrix', 'qbit', 'imaginary', 'numerical')"""

        # Retrieve **kwargs
        expect = kwargs.get('expect', '')
        options = kwargs.get('options', [])

        # Symmath check expects a string of options
        options_str = ",".join(options)

        # Construct the <symbolicresponse> element
        response_element = etree.Element('symbolicresponse')

        if expect:
            response_element.set('expect', str(expect))

        if options_str:
            response_element.set('options', str(options_str))

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)


class ChoiceTextResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <choicetextresponse> xml """

    def create_response_element(self, **kwargs):
        """ Create a <choicetextresponse> element """
        return etree.Element("choicetextresponse")

    def create_input_element(self, **kwargs):
        """ Create a <checkboxgroup> element.
        choices can be specified in the following format:
        [("true", [{"answer": "5", "tolerance": 0}]),
        ("false", [{"answer": "5", "tolerance": 0}])
        ]

        This indicates that the first checkbox/radio is correct and it
        contains a numtolerance_input with an answer of 5 and a tolerance of 0

        It also indicates that the second has a second incorrect radiobutton
        or checkbox with a numtolerance_input.
        """
        choices = kwargs.get('choices', [("true", {})])
        choice_inputs = []
        # Ensure that the first element of choices is an ordered
        # collection. It will start as a list, a tuple, or not a Container.
        if not isinstance(choices[0], (list, tuple)):
            choices = [choices]

        for choice in choices:
            correctness, answers = choice
            numtolerance_inputs = []
            # If the current `choice` contains any("answer": number)
            # elements, turn those into numtolerance_inputs
            if answers:
                # `answers` will be a list or tuple of answers or a single
                # answer, representing the answers for numtolerance_inputs
                # inside of this specific choice.

                # Make sure that `answers` is an ordered collection for
                # convenience.
                if not isinstance(answers, (list, tuple)):
                    answers = [answers]

                numtolerance_inputs = [
                    self._create_numtolerance_input_element(answer)
                    for answer in answers
                ]

            choice_inputs.append(
                self._create_choice_element(
                    correctness=correctness,
                    inputs=numtolerance_inputs
                )
            )
        # Default type is 'radiotextgroup'
        input_type = kwargs.get('type', 'radiotextgroup')
        input_element = etree.Element(input_type)

        for ind, choice in enumerate(choice_inputs):
            # Give each choice text equal to it's position(0,1,2...)
            choice.text = "choice_{0}".format(ind)
            input_element.append(choice)

        return input_element

    def _create_choice_element(self, **kwargs):
        """
        Creates a choice element for a choictextproblem.
        Defaults to a correct choice with no numtolerance_input
        """
        text = kwargs.get('text', '')
        correct = kwargs.get('correctness', "true")
        inputs = kwargs.get('inputs', [])
        choice_element = etree.Element("choice")
        choice_element.set("correct", correct)
        choice_element.text = text
        for inp in inputs:
            # Add all of the inputs as children of this choice
            choice_element.append(inp)

        return choice_element

    def _create_numtolerance_input_element(self, params):
        """
        Creates a <numtolerance_input/>  or <decoy_input/> element with
        optionally specified tolerance and answer.
        """
        answer = params['answer'] if 'answer' in params else None
        # If there is not an answer specified, Then create a <decoy_input/>
        # otherwise create a <numtolerance_input/> and set its tolerance
        # and answer attributes.
        if answer:
            text_input = etree.Element("numtolerance_input")
            text_input.set('answer', answer)
            # If tolerance was specified, was specified use it, otherwise
            # Set the tolerance to "0"
            text_input.set(
                'tolerance',
                params['tolerance'] if 'tolerance' in params else "0"
            )

        else:
            text_input = etree.Element("decoy_input")

        return text_input
