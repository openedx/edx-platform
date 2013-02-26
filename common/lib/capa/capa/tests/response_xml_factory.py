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

        *num_inputs*: The number of input elements
            to create [DEFAULT: 1]

        Returns a string representation of the XML tree.
        """

        # Retrieve keyward arguments
        question_text = kwargs.get('question_text', '')
        explanation_text = kwargs.get('explanation_text', '')
        script = kwargs.get('script', None)
        num_inputs = kwargs.get('num_inputs', 1)

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

        # Add the response
        response_element = self.create_response_element(**kwargs)
        root.append(response_element)
        
        # Add input elements
        for i in range(0, int(num_inputs)):
            input_element = self.create_input_element(**kwargs)
            response_element.append(input_element)

        # The problem has an explanation of the solution
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
        """
        # Names of group elements
        group_element_names = {'checkbox': 'checkboxgroup',
                                'radio': 'radiogroup',
                                'multiple': 'choicegroup' }

        # Retrieve **kwargs
        choices = kwargs.get('choices', [True])
        choice_type = kwargs.get('choice_type', 'multiple')
        choice_names = kwargs.get('choice_names', [None] * len(choices))

        # Create the <choicegroup>, <checkboxgroup>, or <radiogroup> element
        assert(choice_type in group_element_names)
        group_element = etree.Element(group_element_names[choice_type])

        # Create the <choice> elements
        for (correct_val, name) in zip(choices, choice_names):
            choice_element = etree.SubElement(group_element, "choice")
            choice_element.set("correct", "true" if correct_val else "false")

            # Add some text describing the choice
            etree.SubElement(choice_element, "startouttext")
            etree.text = "Choice description"
            etree.SubElement(choice_element, "endouttext")

            # Add a name identifying the choice, if one exists
            if name:
                choice_element.set("name", str(name))

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
        """

        answer = kwargs.get('answer', None)
        tolerance = kwargs.get('tolerance', None)

        response_element = etree.Element('numericalresponse')

        if answer:
            response_element.set('answer', str(answer))

        if tolerance:
            responseparam_element = etree.SubElement(response_element, 'responseparam')
            responseparam_element.set('type', 'tolerance')
            responseparam_element.set('default', str(tolerance))

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

        # Create the response element
        response_element = etree.Element("customresponse")

        if cfn:
            response_element.set('cfn', str(cfn))

        if expect:
            response_element.set('expect', str(expect))

        if answer:
            answer_element = etree.SubElement(response_element, "answer")
            answer_element.text = str(answer)

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

    def create_response_element(self, **kwargs):
        """ Create a <coderesponse> XML element """
        raise NotImplemented

    def create_input_element(self, **kwargs):
        raise NotImplemented


class ChoiceResponseXMLFactory(ResponseXMLFactory):
    def create_response_element(self, **kwargs):
        """ Create a <choiceresponse> element """
        return etree.Element("choiceresponse")

    def create_input_element(self, **kwargs):
        """ Create a <checkboxgroup> element."""
        return ResponseXMLFactory.choicegroup_input_xml(**kwargs)


class FormulaResponseXMLFactory(ResponseXMLFactory):
    def create_response_element(self, **kwargs):
        raise NotImplemented

    def create_input_element(self, **kwargs):
        raise NotImplemented

class ImageResponseXMLFactory(ResponseXMLFactory):
    def create_response_element(self, **kwargs):
        raise NotImplemented

    def create_input_element(self, **kwargs):
        raise NotImplemented

class JavascriptResponseXMLFactory(ResponseXMLFactory):
    def create_response_element(self, **kwargs):
        raise NotImplemented

    def create_input_element(self, **kwargs):
        raise NotImplemented

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

        assert(options_list and correct_option)
        assert(len(options_list) > 1)
        assert(correct_option in options_list)

        # Create the <optioninput> element
        optioninput_element = etree.Element("optioninput")

        # Set the "options" attribute
        # Format: "('first', 'second', 'third')"
        options_attr_string = ",".join(["'%s'" % str(o) for o in options_list])
        options_attr_string = "(%s)" % options_attr_string
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
        """
        # Retrieve the **kwargs
        answer = kwargs.get("answer", None)
        case_sensitive = kwargs.get("case_sensitive", True)
        hint_list = kwargs.get('hints', None)
        assert(answer)

        # Create the <stringresponse> element
        response_element = etree.Element("stringresponse")

        # Set the answer attribute 
        response_element.set("answer", str(answer))

        # Set the case sensitivity
        response_element.set("type", "cs" if case_sensitive else "ci")

        # Add the hints if specified
        if hint_list:
            hintgroup_element = etree.SubElement(response_element, "hintgroup")
            for (hint_prompt, hint_name, hint_text) in hint_list:
                stringhint_element = etree.SubElement(hintgroup_element, "stringhint")
                stringhint_element.set("answer", str(hint_prompt))
                stringhint_element.set("name", str(hint_name))

                hintpart_element = etree.SubElement(hintgroup_element, "hintpart")
                hintpart_element.set("on", str(hint_name))

                hint_text_element = etree.SubElement(hintpart_element, "text")
                hint_text_element.text = str(hint_text)

        return response_element

    def create_input_element(self, **kwargs):
        return ResponseXMLFactory.textline_input_xml(**kwargs)


class SymbolicResponseXMLFactory(ResponseXMLFactory):
    def create_response_element(self, **kwargs):
        raise NotImplemented

    def create_input_element(self, **kwargs):
        raise NotImplemented
