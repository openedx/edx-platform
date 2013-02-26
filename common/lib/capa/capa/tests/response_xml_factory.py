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

        'question_text': The text of the question to display,
            wrapped in <p> tags.
        
        'explanation_text': The detailed explanation that will
            be shown if the user answers incorrectly.

        'script': The embedded Python script (a string)

        'num_inputs': The number of input elements
            to create [DEFAULT: 1]

        Returns a string representation of the XML tree.
        """

        # Retrieve keyward arguments
        question_text = kwargs.get('question_text', '')
        explanation_text = kwargs.get('explanation_text')
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

        'math_display': If True, then includes a MathJax display of user input

        'size': An integer representing the width of the text line
        """
        math_display = kwargs.get('math_display', False)
        size = kwargs.get('size', None)

        input_element = etree.Element('textline')

        if math_display:
            input_element.set('math', '1')

        if size:
            input_element.set('size', str(size))

        return input_element

class NumericalResponseXMLFactory(ResponseXMLFactory):
    """ Factory for producing <numericalresponse> XML trees """

    def create_response_element(self, **kwargs):
        """ Create a <numericalresponse> XML element.
        Uses **kwarg keys:

        'answer': The correct answer (e.g. "5")

        'tolerance': The tolerance within which a response
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

        Use **kwargs:

        'cfn': the Python code to run.  Can be inline code,
        or the name of a function defined in earlier <script> tags.

        Should have the form: cfn(expect, ans)
        where expect is a value (see below) 
        and ans is a list of values.

        'expect': The value passed as the first argument to the function cfn

        'answer': Inline script that calculates the answer
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
