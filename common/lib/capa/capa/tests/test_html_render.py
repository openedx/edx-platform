import unittest
from lxml import etree
import os
import textwrap

import mock

from .response_xml_factory import StringResponseXMLFactory, CustomResponseXMLFactory
from . import test_capa_system, new_loncapa_problem


class CapaHtmlRenderTest(unittest.TestCase):

    def setUp(self):
        super(CapaHtmlRenderTest, self).setUp()
        self.capa_system = test_capa_system()

    def test_blank_problem(self):
        """
        It's important that blank problems don't break, since that's
        what you start with in studio.
        """
        xml_str = "<problem> </problem>"

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        etree.XML(problem.get_html())
        # TODO: This test should inspect the rendered html and assert one or more things about it

    def test_include_html(self):
        # Create a test file to include
        self._create_test_file(
            'test_include.xml',
            '<test>Test include</test>'
        )

        # Generate some XML with an <include>
        xml_str = textwrap.dedent("""
            <problem>
                <include file="test_include.xml"/>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str, capa_system=self.capa_system)

        # Render the HTML
        rendered_html = etree.XML(problem.get_html())

        # Expect that the include file was embedded in the problem
        test_element = rendered_html.find("test")
        self.assertEqual(test_element.tag, "test")
        self.assertEqual(test_element.text, "Test include")

    def test_process_outtext(self):
        # Generate some XML with <startouttext /> and <endouttext />
        xml_str = textwrap.dedent("""
            <problem>
            <startouttext/>Test text<endouttext/>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        rendered_html = etree.XML(problem.get_html())

        # Expect that the <startouttext /> and <endouttext />
        # were converted to <span></span> tags
        span_element = rendered_html.find('span')
        self.assertEqual(span_element.text, 'Test text')

    def test_anonymous_student_id(self):
        # make sure anonymous_student_id is rendered properly as a context variable
        xml_str = textwrap.dedent("""
            <problem>
            <span>Welcome $anonymous_student_id</span>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        rendered_html = etree.XML(problem.get_html())

        # Expect that the anonymous_student_id was converted to "student"
        span_element = rendered_html.find('span')
        self.assertEqual(span_element.text, 'Welcome student')

    def test_render_script(self):
        # Generate some XML with a <script> tag
        xml_str = textwrap.dedent("""
            <problem>
                <script>test=True</script>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        rendered_html = etree.XML(problem.get_html())

        # Expect that the script element has been removed from the rendered HTML
        script_element = rendered_html.find('script')
        self.assertEqual(None, script_element)

    def test_render_javascript(self):
        # Generate some XML with a <script> tag
        xml_str = textwrap.dedent("""
            <problem>
                <script type="text/javascript">function(){}</script>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        rendered_html = etree.XML(problem.get_html())

        # expect the javascript is still present in the rendered html
        self.assertIn(
            "<script type=\"text/javascript\">function(){}</script>",
            etree.tostring(rendered_html)
        )

    def test_render_response_xml(self):
        # Generate some XML for a string response
        kwargs = {
            'question_text': "Test question",
            'explanation_text': "Test explanation",
            'answer': 'Test answer',
            'hints': [('test prompt', 'test_hint', 'test hint text')]
        }
        xml_str = StringResponseXMLFactory().build_xml(**kwargs)

        # Mock out the template renderer
        the_system = test_capa_system()
        the_system.render_template = mock.Mock()
        the_system.render_template.return_value = "<div>Input Template Render</div>"

        # Create the problem and render the HTML
        problem = new_loncapa_problem(xml_str, capa_system=the_system)
        rendered_html = etree.XML(problem.get_html())

        # Expect problem has been turned into a <div>
        self.assertEqual(rendered_html.tag, "div")

        # Expect that the response has been turned into a <section> with correct attributes
        response_element = rendered_html.find("section")
        self.assertEqual(response_element.tag, "section")
        self.assertEqual(response_element.attrib["aria-label"], "Question 1")

        # Expect that the response <section>
        # that contains a <div> for the textline
        textline_element = response_element.find("div")
        self.assertEqual(textline_element.text, 'Input Template Render')

        # Expect a child <div> for the solution
        # with the rendered template
        solution_element = rendered_html.find("div")
        self.assertEqual(solution_element.text, 'Input Template Render')

        # Expect that the template renderer was called with the correct
        # arguments, once for the textline input and once for
        # the solution
        expected_textline_context = {
            'STATIC_URL': '/dummy-static/',
            'status': the_system.STATUS_CLASS('unsubmitted'),
            'value': '',
            'preprocessor': None,
            'msg': '',
            'inline': False,
            'hidden': False,
            'do_math': False,
            'id': '1_2_1',
            'trailing_text': '',
            'size': None,
            'response_data': {'label': 'Test question', 'descriptions': {}},
            'describedby': ''
        }

        expected_solution_context = {'id': '1_solution_1'}

        expected_calls = [
            mock.call('textline.html', expected_textline_context),
            mock.call('solutionspan.html', expected_solution_context),
            mock.call('textline.html', expected_textline_context),
            mock.call('solutionspan.html', expected_solution_context)
        ]

        self.assertEqual(
            the_system.render_template.call_args_list,
            expected_calls
        )

    def test_correct_aria_label(self):
        xml = """
                 <problem>
                     <choiceresponse>
                         <checkboxgroup>
                             <choice correct="true">over-suspicious</choice>
                             <choice correct="false">funny</choice>
                         </checkboxgroup>
                     </choiceresponse>
                     <choiceresponse>
                         <checkboxgroup>
                             <choice correct="true">Urdu</choice>
                             <choice correct="false">Finnish</choice>
                         </checkboxgroup>
                     </choiceresponse>
                 </problem>
                 """
        problem = new_loncapa_problem(xml)
        rendered_html = etree.XML(problem.get_html())
        sections = rendered_html.findall('section')
        self.assertEqual(sections[0].attrib['aria-label'], 'Question 1')
        self.assertEqual(sections[1].attrib['aria-label'], 'Question 2')

    def test_render_response_with_overall_msg(self):
        # CustomResponse script that sets an overall_message
        script = textwrap.dedent("""
            def check_func(*args):
                msg = '<p>Test message 1<br /></p><p>Test message 2</p>'
                return {'overall_message': msg,
                        'input_list': [ {'ok': True, 'msg': '' } ] }
        """)

        # Generate some XML for a CustomResponse
        kwargs = {'script': script, 'cfn': 'check_func'}
        xml_str = CustomResponseXMLFactory().build_xml(**kwargs)

        # Create the problem and render the html
        problem = new_loncapa_problem(xml_str)

        # Grade the problem
        problem.grade_answers({'1_2_1': 'test'})

        # Render the html
        rendered_html = etree.XML(problem.get_html())

        # Expect that there is a <div> within the response <div>
        # with css class response_message
        msg_div_element = rendered_html.find(".//div[@class='response_message']")
        self.assertEqual(msg_div_element.tag, "div")
        self.assertEqual(msg_div_element.get('class'), "response_message")

        # Expect that the <div> contains our message (as part of the XML tree)
        msg_p_elements = msg_div_element.findall('p')
        self.assertEqual(msg_p_elements[0].tag, "p")
        self.assertEqual(msg_p_elements[0].text, "Test message 1")

        self.assertEqual(msg_p_elements[1].tag, "p")
        self.assertEqual(msg_p_elements[1].text, "Test message 2")

    def test_substitute_python_vars(self):
        # Generate some XML with Python variables defined in a script
        # and used later as attributes
        xml_str = textwrap.dedent("""
            <problem>
                <script>test="TEST"</script>
                <span attr="$test"></span>
            </problem>
        """)

        # Create the problem and render the HTML
        problem = new_loncapa_problem(xml_str)
        rendered_html = etree.XML(problem.get_html())

        # Expect that the variable $test has been replaced with its value
        span_element = rendered_html.find('span')
        self.assertEqual(span_element.get('attr'), "TEST")

    def test_xml_comments_and_other_odd_things(self):
        # Comments and processing instructions should be skipped.
        xml_str = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <!DOCTYPE html [
                <!ENTITY % wacky "lxml.etree is wacky!">
            ]>
            <problem>
            <!-- A commment. -->
            <?ignore this processing instruction. ?>
            </problem>
        """)

        # Create the problem
        problem = new_loncapa_problem(xml_str)

        # Render the HTML
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>\s+</div>")

    def _create_test_file(self, path, content_str):
        test_fp = self.capa_system.filestore.open(path, "w")
        test_fp.write(content_str)
        test_fp.close()

        self.addCleanup(lambda: os.remove(test_fp.name))
