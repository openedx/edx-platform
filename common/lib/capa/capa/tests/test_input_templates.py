"""Tests for the logic in input type mako templates."""
#pylint: disable=R0904

import unittest
import capa
import os.path
from lxml import etree
from mako.template import Template as MakoTemplate


class TemplateTestCase(unittest.TestCase):
    """Utilitites for testing templates"""

    # Allow us to pass an extra arg to setUp to configure
    # the test case.  Also allow setUp as a valid method name.
    #pylint: disable=W0221
    #pylint: disable=C0103
    def setUp(self, template_name):
        """Load the template

        `template_name` is the file name of the template
        to be loaded from capa/templates.
        The template name should include the .html extension:
        for example: choicegroup.html
        """
        capa_path = capa.__path__[0]
        self.template_path = os.path.join(capa_path, 'templates', template_name)
        template_file = open(self.template_path)
        self.template = MakoTemplate(template_file.read())
        template_file.close()

    # Allow us to pass **context_dict to render_unicode()
    #pylint: disable=W0142
    def render_to_xml(self, context_dict):
        """Render the template using the `context_dict` dict.

        Returns an `etree` XML element."""
        xml_str = self.template.render_unicode(**context_dict)
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


class TestChoiceGroupTemplate(TemplateTestCase):
    """Test mako template for `<choicegroup>` input"""

    # Allow us to pass an extra arg to setUp to configure
    # the test case.  Also allow setUp as a valid method name.
    #pylint: disable=W0221
    #pylint: disable=C0103
    def setUp(self):
        choices = [('1', 'choice 1'), ('2', 'choice 2'), ('3', 'choice 3')]
        self.context = {'id': '1',
                        'choices': choices,
                        'status': 'correct',
                        'input_type': 'checkbox',
                        'name_array_suffix': '1',
                        'value': '3'}
        super(TestChoiceGroupTemplate, self).setUp('choicegroup.html')

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

    def test_problem_marked_unanswered(self):
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
            message_elements = xml.xpath("//div[@class='capa_alert']")
            self.assertEqual(len(message_elements), 1)
            self.assertEqual(message_elements[0].text,
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
