"""
Tests for the logic in input type mako templates.
"""

import unittest
import capa
import os.path
import json
from lxml import etree
from mako.template import Template as MakoTemplate
from mako import exceptions
from capa.inputtypes import Status


class TemplateError(Exception):
    """
    Error occurred while rendering a Mako template.
    """
    pass


class TemplateTestCase(unittest.TestCase):
    """
    Utilitites for testing templates.
    """

    # Subclasses override this to specify the file name of the template
    # to be loaded from capa/templates.
    # The template name should include the .html extension:
    # for example: choicegroup.html
    TEMPLATE_NAME = None

    def setUp(self):
        """
        Load the template under test.
        """
        super(TemplateTestCase, self).setUp()
        capa_path = capa.__path__[0]
        self.template_path = os.path.join(capa_path,
                                          'templates',
                                          self.TEMPLATE_NAME)
        with open(self.template_path) as f:
            self.template = MakoTemplate(f.read())

    def render_to_xml(self, context_dict):
        """
        Render the template using the `context_dict` dict.
        Returns an `etree` XML element.
        """
        # add dummy STATIC_URL to template context
        context_dict.setdefault("STATIC_URL", "/dummy-static/")
        try:
            xml_str = self.template.render_unicode(**context_dict)
        except:
            raise TemplateError(exceptions.text_error_template().render())

        # Attempt to construct an XML tree from the template
        # This makes it easy to use XPath to make assertions, rather
        # than dealing with a string.
        # We modify the string slightly by wrapping it in <test>
        # tags, to ensure it has one root element.
        try:
            xml = etree.fromstring("<test>" + xml_str + "</test>")
        except Exception as exc:
            raise TemplateError("Could not parse XML from '{0}': {1}".format(
                                xml_str, str(exc)))
        else:
            return xml

    def assert_has_xpath(self, xml_root, xpath, context_dict, exact_num=1):
        """
        Asserts that the xml tree has an element satisfying `xpath`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `context` is used to print a debugging message
        `exact_num` is the exact number of matches to expect.
        """
        message = ("XML does not have %d match(es) for xpath '%s'\nXML: %s\nContext: %s"
                   % (exact_num, str(xpath), etree.tostring(xml_root), str(context_dict)))

        self.assertEqual(len(xml_root.xpath(xpath)), exact_num, msg=message)

    def assert_no_xpath(self, xml_root, xpath, context_dict):
        """
        Asserts that the xml tree does NOT have an element
        satisfying `xpath`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `context` is used to print a debugging message
        """
        self.assert_has_xpath(xml_root, xpath, context_dict, exact_num=0)

    def assert_has_text(self, xml_root, xpath, text, exact=True):
        """
        Find the element at `xpath` in `xml_root` and assert
        that its text is `text`.

        `xml_root` is an etree XML element
        `xpath` is an XPath string, such as `'/foo/bar'`
        `text` is the expected text that the element should contain

        If multiple elements are found, checks the first one.
        If no elements are found, the assertion fails.
        """
        element_list = xml_root.xpath(xpath)
        self.assertGreater(len(element_list), 0, "Could not find element at '%s'" % str(xpath))

        if exact:
            self.assertEqual(text, element_list[0].text)
        else:
            self.assertIn(text, element_list[0].text)


class ChoiceGroupTemplateTest(TemplateTestCase):
    """
    Test mako template for `<choicegroup>` input.
    """

    TEMPLATE_NAME = 'choicegroup.html'

    def setUp(self):
        choices = [('1', 'choice 1'), ('2', 'choice 2'), ('3', 'choice 3')]
        self.context = {
            'id': '1',
            'choices': choices,
            'status': Status('correct'),
            'label': 'test',
            'input_type': 'checkbox',
            'name_array_suffix': '1',
            'value': '3',
            'response_data': {'label': 'test'}
        }
        super(ChoiceGroupTemplateTest, self).setUp()

    def test_problem_marked_correct(self):
        """
        Test conditions under which the entire problem
        (not a particular option) is marked correct.
        """

        self.context['status'] = Status('correct')
        self.context['input_type'] = 'checkbox'
        self.context['value'] = ['1', '2']

        # Should mark the entire problem correct
        xml = self.render_to_xml(self.context)
        xpath = "//div[@class='indicator-container']/span[@class='status correct']"
        self.assert_has_xpath(xml, xpath, self.context)

        # Should NOT mark individual options
        self.assert_no_xpath(xml, "//label[@class='choicegroup_incorrect']",
                             self.context)

        self.assert_no_xpath(xml, "//label[@class='choicegroup_correct']",
                             self.context)

    def test_problem_marked_incorrect(self):
        """
        Test all conditions under which the entire problem
        (not a particular option) is marked incorrect.
        """
        conditions = [
            {'status': Status('incorrect'), 'input_type': 'radio', 'value': ''},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': []},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': ['2']},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': ['2', '3']},
            {'status': Status('incomplete'), 'input_type': 'radio', 'value': ''},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': []},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': ['2']},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': ['2', '3']}]

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator-container']/span[@class='status incorrect']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_incorrect']",
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_correct']",
                                 self.context)

    def test_problem_marked_unsubmitted(self):
        """
        Test all conditions under which the entire problem
        (not a particular option) is marked unanswered.
        """
        conditions = [
            {'status': Status('unsubmitted'), 'input_type': 'radio', 'value': ''},
            {'status': Status('unsubmitted'), 'input_type': 'radio', 'value': []},
            {'status': Status('unsubmitted'), 'input_type': 'checkbox', 'value': []},
            {'input_type': 'radio', 'value': ''},
            {'input_type': 'radio', 'value': []},
            {'input_type': 'checkbox', 'value': []},
            {'input_type': 'checkbox', 'value': ['1']},
            {'input_type': 'checkbox', 'value': ['1', '2']}]

        self.context['status'] = Status('unanswered')

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator-container']/span[@class='status unanswered']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_incorrect']",
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//label[@class='choicegroup_correct']",
                                 self.context)

    def test_option_marked_correct(self):
        """
        Test conditions under which a particular option
        (not the entire problem) is marked correct.
        """
        conditions = [
            {'input_type': 'radio', 'value': '2'},
            {'input_type': 'radio', 'value': ['2']}]

        self.context['status'] = Status('correct')

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//label[contains(@class, 'choicegroup_correct')]"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator-container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_option_marked_incorrect(self):
        """
        Test conditions under which a particular option
        (not the entire problem) is marked incorrect.
        """
        conditions = [
            {'input_type': 'radio', 'value': '2'},
            {'input_type': 'radio', 'value': ['2']}]

        self.context['status'] = Status('incorrect')

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//label[contains(@class, 'choicegroup_incorrect')]"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator-container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_never_show_correctness(self):
        """
        Test conditions under which we tell the template to
        NOT show correct/incorrect, but instead show a message.

        This is used, for example, by the Justice course to ask
        questions without specifying a correct answer.  When
        the student responds, the problem displays "Thank you
        for your response"
        """

        conditions = [
            {'input_type': 'radio', 'status': Status('correct'), 'value': ''},
            {'input_type': 'radio', 'status': Status('correct'), 'value': '2'},
            {'input_type': 'radio', 'status': Status('correct'), 'value': ['2']},
            {'input_type': 'radio', 'status': Status('incorrect'), 'value': '2'},
            {'input_type': 'radio', 'status': Status('incorrect'), 'value': []},
            {'input_type': 'radio', 'status': Status('incorrect'), 'value': ['2']},
            {'input_type': 'checkbox', 'status': Status('correct'), 'value': []},
            {'input_type': 'checkbox', 'status': Status('correct'), 'value': ['2']},
            {'input_type': 'checkbox', 'status': Status('incorrect'), 'value': []},
            {'input_type': 'checkbox', 'status': Status('incorrect'), 'value': ['2']}]

        self.context['show_correctness'] = 'never'
        self.context['submitted_message'] = 'Test message'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)

            # Should NOT mark the entire problem correct/incorrect
            xpath = "//div[@class='indicator-container']/span[@class='status correct']"
            self.assert_no_xpath(xml, xpath, self.context)

            xpath = "//div[@class='indicator-container']/span[@class='status incorrect']"
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
        """
        Ensure that we don't show the `submitted_message`
        before submitting.
        """

        conditions = [
            {'input_type': 'radio', 'status': Status('unsubmitted'), 'value': ''},
            {'input_type': 'radio', 'status': Status('unsubmitted'), 'value': []},
            {'input_type': 'checkbox', 'status': Status('unsubmitted'), 'value': []},

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

    def test_label(self):
        xml = self.render_to_xml(self.context)
        xpath = "//legend"
        self.assert_has_text(xml, xpath, self.context['label'])


class TextlineTemplateTest(TemplateTestCase):
    """
    Test mako template for `<textline>` input.
    """

    TEMPLATE_NAME = 'textline.html'

    def setUp(self):
        self.context = {'id': '1',
                        'status': Status('correct'),
                        'label': 'test',
                        'value': '3',
                        'preprocessor': None,
                        'trailing_text': None}
        super(TextlineTemplateTest, self).setUp()

    def test_section_class(self):
        cases = [({}, ' capa_inputtype  textline'),
                 ({'do_math': True}, 'text-input-dynamath capa_inputtype  textline'),
                 ({'inline': True}, ' capa_inputtype inline textline'),
                 ({'do_math': True, 'inline': True}, 'text-input-dynamath capa_inputtype inline textline'), ]

        for (context, css_class) in cases:
            base_context = self.context.copy()
            base_context.update(context)
            xml = self.render_to_xml(base_context)
            xpath = "//div[@class='%s']" % css_class
            self.assert_has_xpath(xml, xpath, self.context)

    def test_status(self):
        cases = [('correct', 'correct', 'correct'),
                 ('unsubmitted', 'unanswered', 'unanswered'),
                 ('incorrect', 'incorrect', 'incorrect'),
                 ('incomplete', 'incorrect', 'incomplete')]

        for (context_status, div_class, status_mark) in cases:
            self.context['status'] = Status(context_status)
            xml = self.render_to_xml(self.context)

            # Expect that we get a <div> with correct class
            xpath = "//div[@class='%s ']" % div_class
            self.assert_has_xpath(xml, xpath, self.context)

            # Expect that we get a <span> with class="status"
            # (used to by CSS to draw the green check / red x)
            self.assert_has_text(xml, "//span[@class='status']/span[@class='sr']",
                                 status_mark, exact=False)

    def test_label(self):
        xml = self.render_to_xml(self.context)
        xpath = "//input[@aria-label='%s']" % self.context['label']
        self.assert_has_xpath(xml, xpath, self.context)

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

        xpath = "//div[contains(@class, 'text-input-dynamath_data') and @data-preprocessor='test_class']"
        self.assert_has_xpath(xml, xpath, self.context)

        xpath = "//div[@class='script_placeholder' and @data-src='test_script']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_do_inline_and_preprocessor(self):
        self.context['preprocessor'] = {'class_name': 'test_class',
                                        'script_src': 'test_script'}
        self.context['inline'] = True
        xml = self.render_to_xml(self.context)

        xpath = "//div[contains(@class, 'text-input-dynamath_data inline') and @data-preprocessor='test_class']"
        self.assert_has_xpath(xml, xpath, self.context)

    def test_do_inline(self):
        cases = [('correct', 'correct'),
                 ('unsubmitted', 'unanswered'),
                 ('incorrect', 'incorrect'),
                 ('incomplete', 'incorrect')]

        self.context['inline'] = True

        for (context_status, div_class) in cases:
            self.context['status'] = Status(context_status)
            xml = self.render_to_xml(self.context)

            # Expect that we get a <div> with correct class
            xpath = "//div[@class='%s inline']" % div_class
            self.assert_has_xpath(xml, xpath, self.context)

    def test_message(self):
        self.context['msg'] = "Test message"
        xml = self.render_to_xml(self.context)

        xpath = "//span[@class='message']"
        self.assert_has_text(xml, xpath, self.context['msg'])


class FormulaEquationInputTemplateTest(TemplateTestCase):
    """
    Test make template for `<formulaequationinput>`s.
    """
    TEMPLATE_NAME = 'formulaequationinput.html'

    def setUp(self):
        self.context = {
            'id': 2,
            'value': 'PREFILLED_VALUE',
            'status': Status('unsubmitted'),
            'label': 'test',
            'previewer': 'file.js',
            'reported_status': 'REPORTED_STATUS',
            'trailing_text': None,
        }
        super(FormulaEquationInputTemplateTest, self).setUp()

    def test_no_size(self):
        xml = self.render_to_xml(self.context)
        self.assert_no_xpath(xml, "//input[@size]", self.context)

    def test_size(self):
        self.context['size'] = '40'
        xml = self.render_to_xml(self.context)

        self.assert_has_xpath(xml, "//input[@size='40']", self.context)


class AnnotationInputTemplateTest(TemplateTestCase):
    """
    Test mako template for `<annotationinput>` input.
    """

    TEMPLATE_NAME = 'annotationinput.html'

    def setUp(self):
        self.context = {'id': 2,
                        'value': '<p>Test value</p>',
                        'title': '<h1>This is a title</h1>',
                        'text': '<p><b>This</b> is a test.</p>',
                        'comment': '<p>This is a test comment</p>',
                        'comment_prompt': '<p>This is a test comment prompt</p>',
                        'comment_value': '<p>This is the value of a test comment</p>',
                        'tag_prompt': '<p>This is a tag prompt</p>',
                        'options': [],
                        'has_options_value': False,
                        'debug': False,
                        'status': Status('unsubmitted'),
                        'return_to_annotation': False,
                        'msg': '<p>This is a test message</p>', }
        super(AnnotationInputTemplateTest, self).setUp()

    def test_return_to_annotation(self):
        """
        Test link for `Return to Annotation` appears if and only if
        the flag is set.
        """

        xpath = "//a[@class='annotation-return']"

        # If return_to_annotation set, then show the link
        self.context['return_to_annotation'] = True
        xml = self.render_to_xml(self.context)
        self.assert_has_xpath(xml, xpath, self.context)

        # Otherwise, do not show the links
        self.context['return_to_annotation'] = False
        xml = self.render_to_xml(self.context)
        self.assert_no_xpath(xml, xpath, self.context)

    def test_option_selection(self):
        """
        Test that selected options are selected.
        """

        # Create options 0-4 and select option 2
        self.context['options_value'] = [2]
        self.context['options'] = [
            {'id': id_num,
             'choice': 'correct',
             'description': '<p>Unescaped <b>HTML {0}</b></p>'.format(id_num)}
            for id_num in range(5)]

        xml = self.render_to_xml(self.context)

        # Expect that each option description is visible
        # with unescaped HTML.
        # Since the HTML is unescaped, we can traverse the XML tree
        for id_num in range(5):
            xpath = "//span[@data-id='{0}']/p/b".format(id_num)
            self.assert_has_text(xml, xpath, 'HTML {0}'.format(id_num), exact=False)

        # Expect that the correct option is selected
        xpath = "//span[contains(@class,'selected')]/p/b"
        self.assert_has_text(xml, xpath, 'HTML 2', exact=False)

    def test_submission_status(self):
        """
        Test that the submission status displays correctly.
        """

        # Test cases of `(input_status, expected_css_class)` tuples
        test_cases = [('unsubmitted', 'unanswered'),
                      ('incomplete', 'incorrect'),
                      ('incorrect', 'incorrect')]

        for (input_status, expected_css_class) in test_cases:
            self.context['status'] = Status(input_status)
            xml = self.render_to_xml(self.context)

            xpath = "//span[@class='status {0}']".format(expected_css_class)
            self.assert_has_xpath(xml, xpath, self.context)

        # If individual options are being marked, then expect
        # just the option to be marked incorrect, not the whole problem
        self.context['has_options_value'] = True
        self.context['status'] = Status('incorrect')
        xpath = "//span[@class='incorrect']"
        xml = self.render_to_xml(self.context)
        self.assert_no_xpath(xml, xpath, self.context)

    def test_display_html_comment(self):
        """
        Test that HTML comment and comment prompt render.
        """
        self.context['comment'] = "<p>Unescaped <b>comment HTML</b></p>"
        self.context['comment_prompt'] = "<p>Prompt <b>prompt HTML</b></p>"
        self.context['text'] = "<p>Unescaped <b>text</b></p>"
        xml = self.render_to_xml(self.context)

        # Because the HTML is unescaped, we should be able to
        # descend to the <b> tag
        xpath = "//div[@class='block']/p/b"
        self.assert_has_text(xml, xpath, 'prompt HTML')

        xpath = "//div[@class='block block-comment']/p/b"
        self.assert_has_text(xml, xpath, 'comment HTML')

        xpath = "//div[@class='block block-highlight']/p/b"
        self.assert_has_text(xml, xpath, 'text')

    def test_display_html_tag_prompt(self):
        """
        Test that HTML tag prompts render.
        """
        self.context['tag_prompt'] = "<p>Unescaped <b>HTML</b></p>"
        xml = self.render_to_xml(self.context)

        # Because the HTML is unescaped, we should be able to
        # descend to the <b> tag
        xpath = "//div[@class='block']/p/b"
        self.assert_has_text(xml, xpath, 'HTML')


class MathStringTemplateTest(TemplateTestCase):
    """
    Test mako template for `<mathstring>` input.
    """

    TEMPLATE_NAME = 'mathstring.html'

    def setUp(self):
        self.context = {'isinline': False, 'mathstr': '', 'tail': ''}
        super(MathStringTemplateTest, self).setUp()

    def test_math_string_inline(self):
        self.context['isinline'] = True
        self.context['mathstr'] = 'y = ax^2 + bx + c'

        xml = self.render_to_xml(self.context)
        xpath = "//section[@class='math-string']/span[1]"
        self.assert_has_text(xml, xpath,
                             '[mathjaxinline]y = ax^2 + bx + c[/mathjaxinline]')

    def test_math_string_not_inline(self):
        self.context['isinline'] = False
        self.context['mathstr'] = 'y = ax^2 + bx + c'

        xml = self.render_to_xml(self.context)
        xpath = "//section[@class='math-string']/span[1]"
        self.assert_has_text(xml, xpath,
                             '[mathjax]y = ax^2 + bx + c[/mathjax]')

    def test_tail_html(self):
        self.context['tail'] = "<p>This is some <b>tail</b> <em>HTML</em></p>"
        xml = self.render_to_xml(self.context)

        # HTML from `tail` should NOT be escaped.
        # We should be able to traverse it as part of the XML tree
        xpath = "//section[@class='math-string']/span[2]/p/b"
        self.assert_has_text(xml, xpath, 'tail')

        xpath = "//section[@class='math-string']/span[2]/p/em"
        self.assert_has_text(xml, xpath, 'HTML')


class OptionInputTemplateTest(TemplateTestCase):
    """
    Test mako template for `<optioninput>` input.
    """

    TEMPLATE_NAME = 'optioninput.html'

    def setUp(self):
        self.context = {
            'id': 2,
            'options': [],
            'status': Status('unsubmitted'),
            'label': 'test',
            'value': 0
        }
        super(OptionInputTemplateTest, self).setUp()

    def test_select_options(self):

        # Create options 0-4, and select option 2
        self.context['options'] = [(id_num, '<b>Option {0}</b>'.format(id_num))
                                   for id_num in range(5)]
        self.context['value'] = 2

        xml = self.render_to_xml(self.context)

        # Should have a dummy default
        xpath = "//option[@value='option_2_dummy_default']"
        self.assert_has_xpath(xml, xpath, self.context)

        # Should have each of the options, with the correct description
        # The description HTML should NOT be escaped
        # (that's why we descend into the <b> tag)
        for id_num in range(5):
            xpath = "//option[@value='{0}']/b".format(id_num)
            self.assert_has_text(xml, xpath, 'Option {0}'.format(id_num))

        # Should have the correct option selected
        xpath = "//option[@selected='true']/b"
        self.assert_has_text(xml, xpath, 'Option 2')

    def test_status(self):

        # Test cases, where each tuple represents
        # `(input_status, expected_css_class)`
        test_cases = [('unsubmitted', 'status unanswered'),
                      ('correct', 'status correct'),
                      ('incorrect', 'status incorrect'),
                      ('incomplete', 'status incorrect')]

        for (input_status, expected_css_class) in test_cases:
            self.context['status'] = Status(input_status)
            xml = self.render_to_xml(self.context)

            xpath = "//span[@class='{0}']".format(expected_css_class)
            self.assert_has_xpath(xml, xpath, self.context)

    def test_label(self):
        xml = self.render_to_xml(self.context)
        xpath = "//select[@aria-label='%s']" % self.context['label']
        self.assert_has_xpath(xml, xpath, self.context)


class DragAndDropTemplateTest(TemplateTestCase):
    """
    Test mako template for `<draganddropinput>` input.
    """

    TEMPLATE_NAME = 'drag_and_drop_input.html'

    def setUp(self):
        self.context = {'id': 2,
                        'drag_and_drop_json': '',
                        'value': 0,
                        'status': Status('unsubmitted'),
                        'msg': ''}
        super(DragAndDropTemplateTest, self).setUp()

    def test_status(self):

        # Test cases, where each tuple represents
        # `(input_status, expected_css_class, expected_text)`
        test_cases = [('unsubmitted', 'unanswered', 'unanswered'),
                      ('correct', 'correct', 'correct'),
                      ('incorrect', 'incorrect', 'incorrect'),
                      ('incomplete', 'incorrect', 'incomplete')]

        for (input_status, expected_css_class, expected_text) in test_cases:
            self.context['status'] = Status(input_status)
            xml = self.render_to_xml(self.context)

            # Expect a <div> with the status
            xpath = "//div[@class='{0}']".format(expected_css_class)
            self.assert_has_xpath(xml, xpath, self.context)

            # Expect a <p> with the status
            xpath = "//p[@class='status']"
            self.assert_has_text(xml, xpath, expected_text, exact=False)

    def test_drag_and_drop_json_html(self):

        json_with_html = json.dumps({'test': '<p>Unescaped <b>HTML</b></p>'})
        self.context['drag_and_drop_json'] = json_with_html
        xml = self.render_to_xml(self.context)

        # Assert that the JSON-encoded string was inserted without
        # escaping the HTML.  We should be able to traverse the XML tree.
        xpath = "//div[@class='drag_and_drop_problem_json']/p/b"
        self.assert_has_text(xml, xpath, 'HTML')


class ChoiceTextGroupTemplateTest(TemplateTestCase):
    """Test mako template for `<choicetextgroup>` input"""

    TEMPLATE_NAME = 'choicetext.html'
    VALUE_DICT = {'1_choiceinput_0bc': '1_choiceinput_0bc', '1_choiceinput_0_textinput_0': '0',
                  '1_choiceinput_1_textinput_0': '0'}
    EMPTY_DICT = {'1_choiceinput_0_textinput_0': '',
                  '1_choiceinput_1_textinput_0': ''}
    BOTH_CHOICE_CHECKBOX = {'1_choiceinput_0bc': 'choiceinput_0',
                            '1_choiceinput_1bc': 'choiceinput_1',
                            '1_choiceinput_0_textinput_0': '0',
                            '1_choiceinput_1_textinput_0': '0'}
    WRONG_CHOICE_CHECKBOX = {'1_choiceinput_1bc': 'choiceinput_1',
                             '1_choiceinput_0_textinput_0': '0',
                             '1_choiceinput_1_textinput_0': '0'}

    def setUp(self):
        choices = [
            (
                '1_choiceinput_0bc',
                [
                    {'tail_text': '', 'type': 'text', 'value': '', 'contents': ''},
                    {'tail_text': '', 'type': 'textinput', 'value': '', 'contents': 'choiceinput_0_textinput_0'},
                ]
            ),
            (
                '1_choiceinput_1bc',
                [
                    {'tail_text': '', 'type': 'text', 'value': '', 'contents': ''},
                    {'tail_text': '', 'type': 'textinput', 'value': '', 'contents': 'choiceinput_1_textinput_0'},
                ]
            )
        ]
        self.context = {
            'id': '1',
            'choices': choices,
            'status': Status('correct'),
            'input_type': 'radio',
            'label': 'choicetext label',
            'value': self.VALUE_DICT,
        }

        super(ChoiceTextGroupTemplateTest, self).setUp()

    def test_grouping_tag(self):
        """
        Tests whether we are using a section or a label to wrap choice elements.
        Section is used for checkbox, so inputting text does not deselect
        """
        input_tags = ('radio', 'checkbox')
        self.context['status'] = Status('correct')
        xpath = "//section[@id='forinput1_choiceinput_0bc']"

        self.context['value'] = {}
        for input_type in input_tags:
            self.context['input_type'] = input_type
            xml = self.render_to_xml(self.context)
            self.assert_has_xpath(xml, xpath, self.context)

    def test_problem_marked_correct(self):
        """Test conditions under which the entire problem
        (not a particular option) is marked correct"""

        self.context['status'] = Status('correct')
        self.context['input_type'] = 'checkbox'
        self.context['value'] = self.VALUE_DICT

        # Should mark the entire problem correct
        xml = self.render_to_xml(self.context)
        xpath = "//div[@class='indicator-container']/span[@class='status correct']"
        self.assert_has_xpath(xml, xpath, self.context)

        # Should NOT mark individual options
        self.assert_no_xpath(xml, "//label[@class='choicetextgroup_incorrect']",
                             self.context)

        self.assert_no_xpath(xml, "//label[@class='choicetextgroup_correct']",
                             self.context)

    def test_problem_marked_incorrect(self):
        """Test all conditions under which the entire problem
        (not a particular option) is marked incorrect"""
        grouping_tags = {'radio': 'label', 'checkbox': 'section'}
        conditions = [
            {'status': Status('incorrect'), 'input_type': 'radio', 'value': {}},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': self.WRONG_CHOICE_CHECKBOX},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': self.BOTH_CHOICE_CHECKBOX},
            {'status': Status('incorrect'), 'input_type': 'checkbox', 'value': self.VALUE_DICT},
            {'status': Status('incomplete'), 'input_type': 'radio', 'value': {}},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': self.WRONG_CHOICE_CHECKBOX},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': self.BOTH_CHOICE_CHECKBOX},
            {'status': Status('incomplete'), 'input_type': 'checkbox', 'value': self.VALUE_DICT}]

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator-container']/span[@class='status incorrect']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            grouping_tag = grouping_tags[test_conditions['input_type']]
            self.assert_no_xpath(xml,
                                 "//{0}[@class='choicetextgroup_incorrect']".format(grouping_tag),
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//{0}[@class='choicetextgroup_correct']".format(grouping_tag),
                                 self.context)

    def test_problem_marked_unsubmitted(self):
        """Test all conditions under which the entire problem
        (not a particular option) is marked unanswered"""
        grouping_tags = {'radio': 'label', 'checkbox': 'section'}

        conditions = [
            {'status': Status('unsubmitted'), 'input_type': 'radio', 'value': {}},
            {'status': Status('unsubmitted'), 'input_type': 'radio', 'value': self.EMPTY_DICT},
            {'status': Status('unsubmitted'), 'input_type': 'checkbox', 'value': {}},
            {'status': Status('unsubmitted'), 'input_type': 'checkbox', 'value': self.EMPTY_DICT},
            {'status': Status('unsubmitted'), 'input_type': 'checkbox', 'value': self.VALUE_DICT},
            {'status': Status('unsubmitted'), 'input_type': 'checkbox', 'value': self.BOTH_CHOICE_CHECKBOX},
        ]

        self.context['status'] = Status('unanswered')

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//div[@class='indicator-container']/span[@class='status unanswered']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark individual options
            grouping_tag = grouping_tags[test_conditions['input_type']]
            self.assert_no_xpath(xml,
                                 "//{0}[@class='choicetextgroup_incorrect']".format(grouping_tag),
                                 self.context)

            self.assert_no_xpath(xml,
                                 "//{0}[@class='choicetextgroup_correct']".format(grouping_tag),
                                 self.context)

    def test_option_marked_correct(self):
        """Test conditions under which a particular option
        (not the entire problem) is marked correct."""

        conditions = [
            {'input_type': 'radio', 'value': self.VALUE_DICT}]

        self.context['status'] = 'correct'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//section[@id='forinput1_choiceinput_0bc' and\
                    @class='choicetextgroup_correct']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator-container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_option_marked_incorrect(self):
        """Test conditions under which a particular option
        (not the entire problem) is marked incorrect."""

        conditions = [
            {'input_type': 'radio', 'value': self.VALUE_DICT}]

        self.context['status'] = 'incorrect'

        for test_conditions in conditions:
            self.context.update(test_conditions)
            xml = self.render_to_xml(self.context)
            xpath = "//section[@id='forinput1_choiceinput_0bc' and\
                    @class='choicetextgroup_incorrect']"
            self.assert_has_xpath(xml, xpath, self.context)

            # Should NOT mark the whole problem
            xpath = "//div[@class='indicator-container']/span"
            self.assert_no_xpath(xml, xpath, self.context)

    def test_label(self):
        xml = self.render_to_xml(self.context)
        xpath = "//fieldset[@aria-label='%s']" % self.context['label']
        self.assert_has_xpath(xml, xpath, self.context)
