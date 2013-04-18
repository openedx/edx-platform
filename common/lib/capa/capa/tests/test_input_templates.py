"""Tests for the logic in input type mako templates."""

import unittest
import capa
import os.path
from lxml import etree
from mako.template import Template as MakoTemplate
from mako import exceptions


class TemplateError(Exception):
    """Error occurred while rendering a Mako template"""
    pass


class TemplateTestCase(unittest.TestCase):
    """Utilitites for testing templates"""

    # Subclasses override this to specify the file name of the template
    # to be loaded from capa/templates.
    # The template name should include the .html extension:
    # for example: choicegroup.html
    TEMPLATE_NAME = None

    def setUp(self):
        """Load the template"""
        capa_path = capa.__path__[0]
        self.template_path = os.path.join(capa_path,
                                          'templates',
                                          self.TEMPLATE_NAME)
        template_file = open(self.template_path)
        self.template = MakoTemplate(template_file.read())
        template_file.close()

    def render_to_xml(self, context_dict):
        """Render the template using the `context_dict` dict.

        Returns an `etree` XML element."""
        try:
            xml_str = self.template.render_unicode(**context_dict)
        except:
            raise TemplateError(exceptions.text_error_template().render())

        return etree.fromstring(xml_str)

    def assert_has_xpath(self, xml_root, xpath, context_dict, exact_num=1):
        """Asserts that the xml tree has an element satisfying `xpath`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `context` is used to print a debugging message
        `exact_num` is the exact number of matches to expect.
        """
        message = ("XML does not have %d match(es) for xpath '%s'\nXML: %s\nContext: %s"
                   % (exact_num, str(xpath), etree.tostring(xml_root), str(context_dict)))

        self.assertEqual(len(xml_root.xpath(xpath)), exact_num, msg=message)

    def assert_no_xpath(self, xml_root, xpath, context_dict):
        """Asserts that the xml tree does NOT have an element
        satisfying `xpath`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `context` is used to print a debugging message
        """
        self.assert_has_xpath(xml_root, xpath, context_dict, exact_num=0)

    def assert_has_text(self, xml_root, xpath, text, exact=True):
        """Find the element at `xpath` in `xml_root` and assert
        that its text is `text`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `text` is the expected text that the element should contain

        If multiple elements are found, checks the first one.
        If no elements are found, the assertion fails.
        """
        element_list = xml_root.xpath(xpath)
        self.assertTrue(len(element_list) > 0,
                        "Could not find element at '%s'" % str(xpath))

        if exact:
            self.assertEqual(text, element_list[0].text)
        else:
            self.assertIn(text, element_list[0].text)


class ChoiceGroupTemplateTest(TemplateTestCase):
    """Test mako template for `<choicegroup>` input"""

    TEMPLATE_NAME = 'choicegroup.html'

    def setUp(self):
        choices = [('1', 'choice 1'), ('2', 'choice 2'), ('3', 'choice 3')]
        self.context = {'id': '1',
                        'choices': choices,
                        'status': 'correct',
                        'input_type': 'checkbox',
                        'name_array_suffix': '1',
                        'value': '3'}
        super(ChoiceGroupTemplateTest, self).setUp()

    def test_problem_marked_correct(self):
        """Test conditions under which the entire problem
        (not a particular option) is marked correct"""

        self.context['status'] = 'correct'
        self.context['input_type'] = 'checkbox'
        self.context['value'] = ['1', '2']

        # Should mark the entire problem correct
        xml = self.render_to_xml(self.context)
        xpath = "//div[@class='indicator_container']/span[@class='correct']"
        self.assert_has_xpath(xml, xpath, self.context)

        # Should NOT mark individual options
        self.assert_no_xpath(xml, "//label[@class='choicegroup_incorrect']",
                             self.context)

        self.assert_no_xpath(xml, "//label[@class='choicegroup_correct']",
                             self.context)

    def test_problem_marked_incorrect(self):
        """Test all conditions under which the entire problem
        (not a particular option) is marked incorrect"""
        conditions = [
            {'status': 'incorrect', 'input_type': 'radio', 'value': ''},
            {'status': 'incorrect', 'input_type': 'checkbox', 'value': []},
            {'status': 'incorrect', 'input_type': 'checkbox', 'value': ['2']},
            {'status': 'incorrect', 'input_type': 'checkbox', 'value': ['2', '3']},
            {'status': 'incomplete', 'input_type': 'radio', 'value': ''},
            {'status': 'incomplete', 'input_type': 'checkbox', 'value': []},
            {'status': 'incomplete', 'input_type': 'checkbox', 'value': ['2']},
            {'status': 'incomplete', 'input_type': 'checkbox', 'value': ['2', '3']}]

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator_container']/span[@class='incorrect']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_incorrect']",
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_correct']",
                                 self.context)

    def test_problem_marked_unsubmitted(self):
        """Test all conditions under which the entire problem
        (not a particular option) is marked unanswered"""
        conditions = [
            {'status': 'unsubmitted', 'input_type': 'radio', 'value': ''},
            {'status': 'unsubmitted', 'input_type': 'radio', 'value': []},
            {'status': 'unsubmitted', 'input_type': 'checkbox', 'value': []},
            {'input_type': 'radio', 'value': ''},
            {'input_type': 'radio', 'value': []},
            {'input_type': 'checkbox', 'value': []},
            {'input_type': 'checkbox', 'value': ['1']},
            {'input_type': 'checkbox', 'value': ['1', '2']}]

        self.context['status'] = 'unanswered'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator_container']/span[@class='unanswered']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_incorrect']",
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_correct']",
                                 self.context)

    def test_option_marked_correct(self):
        """Test conditions under which a particular option
        (not the entire problem) is marked correct."""
        conditions = [
            {'input_type': 'radio', 'value': '2'},
            {'input_type': 'radio', 'value': ['2']}]

        self.context['status'] = 'correct'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//label[@class='choicegroup_correct']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator_container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_option_marked_incorrect(self):
        """Test conditions under which a particular option
        (not the entire problem) is marked incorrect."""
        conditions = [
            {'input_type': 'radio', 'value': '2'},
            {'input_type': 'radio', 'value': ['2']}]

        self.context['status'] = 'incorrect'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//label[@class='choicegroup_incorrect']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator_container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_never_show_correctness(self):
        """Test conditions under which we tell the template to
        NOT show correct/incorrect, but instead show a message.

        This is used, for example, by the Justice course to ask
        questions without specifying a correct answer.  When
        the student responds, the problem displays "Thank you
        for your response"
        """

        conditions = [
            {'input_type': 'radio', 'status': 'correct', 'value': ''},
            {'input_type': 'radio', 'status': 'correct', 'value': '2'},
            {'input_type': 'radio', 'status': 'correct', 'value': ['2']},
            {'input_type': 'radio', 'status': 'incorrect', 'value': '2'},
            {'input_type': 'radio', 'status': 'incorrect', 'value': []},
            {'input_type': 'radio', 'status': 'incorrect', 'value': ['2']},
            {'input_type': 'checkbox', 'status': 'correct', 'value': []},
            {'input_type': 'checkbox', 'status': 'correct', 'value': ['2']},
            {'input_type': 'checkbox', 'status': 'incorrect', 'value': []},
            {'input_type': 'checkbox', 'status': 'incorrect', 'value': ['2']}]

        self.context['show_correctness'] = 'never'
        self.context['submitted_message'] = 'Test message'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)

            # Should NOT mark the entire problem correct/incorrect
            xpath = "//div[@class='indicator_container']/span[@class='correct']"
            self.assert_no_xpath(xml, xpath, self.context)

            xpath = "//div[@class='indicator_container']/span[@class='incorrect']"
            self.assert_no_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_incorrect']",
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_correct']",
                                 self.context)

            # Expect to see the message
            self.assert_has_text(xml, "//div[@class='capa_alert']",
                                 self.context['submitted_message'])

    def test_no_message_before_submission(self):
        """Ensure that we don't show the `submitted_message`
        before submitting"""

        conditions = [
            {'input_type': 'radio', 'status': 'unsubmitted', 'value': ''},
            {'input_type': 'radio', 'status': 'unsubmitted', 'value': []},
            {'input_type': 'checkbox', 'status': 'unsubmitted', 'value': []},

            # These tests expose bug #365
            # When the bug is fixed, uncomment these cases.
            #{'input_type': 'radio', 'status': 'unsubmitted', 'value': '2'},
            #{'input_type': 'radio', 'status': 'unsubmitted', 'value': ['2']},
            #{'input_type': 'radio', 'status': 'unsubmitted', 'value': '2'},
            #{'input_type': 'radio', 'status': 'unsubmitted', 'value': ['2']},
            #{'input_type': 'checkbox', 'status': 'unsubmitted', 'value': ['2']},
            #{'input_type': 'checkbox', 'status': 'unsubmitted', 'value': ['2']}]
        ]

        self.context['show_correctness'] = 'never'
        self.context['submitted_message'] = 'Test message'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)

            # Expect that we do NOT see the message yet
            self.assert_no_xpath(xml, "//div[@class='capa_alert']", self.context)


class TextlineTemplateTest(TemplateTestCase):
    """Test mako template for `<textline>` input"""

    TEMPLATE_NAME = 'textline.html'

    def setUp(self):
        self.context = {'id': '1',
                        'status': 'correct',
                        'value': '3',
                        'preprocessor': None,
                        'trailing_text': None}
        super(TextlineTemplateTest, self).setUp()

    def test_section_class(self):
        cases = [({}, ' capa_inputtype '),
                 ({'do_math': True}, 'text-input-dynamath capa_inputtype '),
                 ({'inline': True}, ' capa_inputtype inline'),
                 ({'do_math': True, 'inline': True}, 'text-input-dynamath capa_inputtype inline'), ]

        for (context, css_class) in cases:
            base_context = self.context.copy()
            base_context.update(context)
            xml = self.render_to_xml(base_context)
            xpath = "//section[@class='%s']" % css_class
            self.assert_has_xpath(xml, xpath, self.context)

    def test_status(self):
        cases = [('correct', 'correct', 'correct'),
                 ('unsubmitted', 'unanswered', 'unanswered'),
                 ('incorrect', 'incorrect', 'incorrect'),
                 ('incomplete', 'incorrect', 'incomplete')]

        for (context_status, div_class, status_mark) in cases:
            self.context['status'] = context_status
            xml = self.render_to_xml(self.context)

            # Expect that we get a <div> with correct class
            xpath = "//div[@class='%s ']" % div_class
            self.assert_has_xpath(xml, xpath, self.context)

            # Expect that we get a <p> with class="status"
            # (used to by CSS to draw the green check / red x)
            self.assert_has_text(xml, "//p[@class='status']",
                                 status_mark, exact=False)

    def test_hidden(self):
        self.context['hidden'] = True
        xml = self.render_to_xml(self.context)

        xpath = "//div[@style='display:none;']"
        self.assert_has_xpath(xml, xpath, self.context)

        xpath = "//input[@style='display:none;']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_do_math(self):
        self.context['do_math'] = True
        xml = self.render_to_xml(self.context)

        xpath = "//input[@class='math']"
        self.assert_has_xpath(xml, xpath, self.context)

        xpath = "//div[@class='equation']"
        self.assert_has_xpath(xml, xpath, self.context)

        xpath = "//textarea[@id='input_1_dynamath']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_size(self):
        self.context['size'] = '20'
        xml = self.render_to_xml(self.context)

        xpath = "//input[@size='20']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_preprocessor(self):
        self.context['preprocessor'] = {'class_name': 'test_class',
                                        'script_src': 'test_script'}
        xml = self.render_to_xml(self.context)

        xpath = "//div[@class='text-input-dynamath_data' and @data-preprocessor='test_class']"
        self.assert_has_xpath(xml, xpath, self.context)

        xpath = "//div[@class='script_placeholder' and @data-src='test_script']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_do_inline(self):
        cases = [('correct', 'correct'),
                 ('unsubmitted', 'unanswered'),
                 ('incorrect', 'incorrect'),
                 ('incomplete', 'incorrect')]

        self.context['inline'] = True

        for (context_status, div_class) in cases:
            self.context['status'] = context_status
            xml = self.render_to_xml(self.context)

            # Expect that we get a <div> with correct class
            xpath = "//div[@class='%s inline']" % div_class
            self.assert_has_xpath(xml, xpath, self.context)

    def test_message(self):
        self.context['msg'] = "Test message"
        xml = self.render_to_xml(self.context)

        xpath = "//span[@class='message']"
        self.assert_has_text(xml, xpath, self.context['msg'])
