# -*- coding: utf-8 -*-
"""
Tests of input types.

TODO:
- refactor: so much repetive code (have factory methods that build xml elements directly, etc)

- test error cases

- check rendering -- e.g. msg should appear in the rendered output.  If possible, test that
  templates are escaping things properly.


- test unicode in values, parameters, etc.
- test various html escapes
- test funny xml chars -- should never get xml parse error if things are escaped properly.

"""
import json
import textwrap
import unittest
import xml.sax.saxutils as saxutils
from collections import OrderedDict

from capa import inputtypes
from capa.checker import DemoSystem
from capa.tests.helpers import test_capa_system
from capa.xqueue_interface import XQUEUE_TIMEOUT
from lxml import etree
from lxml.html import fromstring
from mock import ANY, patch
from openedx.core.djangolib.markup import HTML
from pyparsing import ParseException

# just a handy shortcut
lookup_tag = inputtypes.registry.get_class_for_tag


DESCRIBEDBY = HTML('aria-describedby="status_{status_id} desc-1 desc-2"')
DESCRIPTIONS = OrderedDict([('desc-1', 'description text 1'), ('desc-2', 'description text 2')])
RESPONSE_DATA = {
    'label': 'question text 101',
    'descriptions': DESCRIPTIONS
}


def quote_attr(s):
    return saxutils.quoteattr(s)[1:-1]  # don't want the outer quotes


class OptionInputTest(unittest.TestCase):
    '''
    Make sure option inputs work
    '''

    def test_rendering(self):
        xml_str = """<optioninput options="('Up','Down','Don't know')" id="sky_input" correct="Up"/>"""
        element = etree.fromstring(xml_str)

        state = {
            'value': 'Down',
            'id': 'sky_input',
            'status': 'answered',
            'default_option_text': 'Select an option',
            'response_data': RESPONSE_DATA
        }
        option_input = lookup_tag('optioninput')(test_capa_system(), element, state)

        context = option_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'sky_input'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'value': 'Down',
            'options': [('Up', 'Up'), ('Down', 'Down'), ('Don\'t know', 'Don\'t know')],
            'status': inputtypes.Status('answered'),
            'msg': '',
            'inline': False,
            'id': prob_id,
            'default_option_text': 'Select an option',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id='sky_input')
        }

        self.assertEqual(context, expected)

    def test_option_parsing(self):
        f = inputtypes.OptionInput.parse_options

        def check(input, options):
            """Take list of options, confirm that output is in the silly doubled format"""
            expected = [(o, o) for o in options]
            self.assertEqual(f(input), expected)

        check("('a','b')", ['a', 'b'])
        check("('a', 'b')", ['a', 'b'])
        check("('a b','b')", ['a b', 'b'])
        check("('My \"quoted\"place','b')", ['My \"quoted\"place', 'b'])
        check(u"('б','в')", [u'б', u'в'])
        check(u"('б', 'в')", [u'б', u'в'])
        check(u"('б в','в')", [u'б в', u'в'])
        check(u"('Мой \"кавыки\"место','в')", [u'Мой \"кавыки\"место', u'в'])

        # check that escaping single quotes with leading backslash (\') properly works
        # note: actual input by user will be hasn\'t but json parses it as hasn\\'t
        check(u"('hasnt','hasn't')", [u'hasnt', u'hasn\'t'])


class ChoiceGroupTest(unittest.TestCase):
    '''
    Test choice groups, radio groups, and checkbox groups
    '''

    def check_group(self, tag, expected_input_type, expected_suffix):
        xml_str = """
  <{tag}>
    <choice correct="false" name="foil1"><text>This is foil One.</text></choice>
    <choice correct="false" name="foil2"><text>This is foil Two.</text></choice>
    <choice correct="true" name="foil3">This is foil Three.</choice>
    <choice correct="false" name="foil4">This is <b>foil</b> Four.</choice>
  </{tag}>
        """.format(tag=tag)
        element = etree.fromstring(xml_str)

        state = {
            'value': 'foil3',
            'id': 'sky_input',
            'status': 'answered',
            'response_data': RESPONSE_DATA
        }

        the_input = lookup_tag(tag)(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access

        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': 'sky_input',
            'value': 'foil3',
            'status': inputtypes.Status('answered'),
            'msg': '',
            'input_type': expected_input_type,
            'choices': [('foil1', '<text>This is foil One.</text>'),
                        ('foil2', '<text>This is foil Two.</text>'),
                        ('foil3', 'This is foil Three.'),
                        ('foil4', 'This is <b>foil</b> Four.'), ],
            'show_correctness': 'always',
            'submitted_message': 'Answer received.',
            'name_array_suffix': expected_suffix,   # what is this for??
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id='sky_input')
        }

        self.assertEqual(context, expected)

    def test_choicegroup(self):
        self.check_group('choicegroup', 'radio', '')

    def test_radiogroup(self):
        self.check_group('radiogroup', 'radio', '[]')

    def test_checkboxgroup(self):
        self.check_group('checkboxgroup', 'checkbox', '[]')


class TextLineTest(unittest.TestCase):
    '''
    Check that textline inputs work, with and without math.
    '''

    def test_rendering(self):
        size = "42"
        xml_str = """<textline id="prob_1_2" size="{size}"/>""".format(size=size)

        element = etree.fromstring(xml_str)

        state = {
            'value': 'BumbleBee',
            'response_data': RESPONSE_DATA
        }
        the_input = lookup_tag('textline')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'BumbleBee',
            'status': inputtypes.Status('unanswered'),
            'size': size,
            'msg': '',
            'hidden': False,
            'inline': False,
            'do_math': False,
            'trailing_text': '',
            'preprocessor': None,
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }
        self.assertEqual(context, expected)

    def test_math_rendering(self):
        size = "42"
        preprocessorClass = "preParty"
        script = "foo/party.js"

        xml_str = """<textline math="True" id="prob_1_2" size="{size}"
        preprocessorClassName="{pp}"
        preprocessorSrc="{sc}"/>""".format(size=size, pp=preprocessorClass, sc=script)

        element = etree.fromstring(xml_str)

        state = {
            'value': 'BumbleBee',
            'response_data': RESPONSE_DATA
        }
        the_input = lookup_tag('textline')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'BumbleBee',
            'status': inputtypes.Status('unanswered'),
            'size': size,
            'msg': '',
            'hidden': False,
            'inline': False,
            'trailing_text': '',
            'do_math': True,
            'preprocessor': {
                'class_name': preprocessorClass,
                'script_src': script,
            },
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }
        self.assertEqual(context, expected)

    def test_trailing_text_rendering(self):
        size = "42"
        # store (xml_text, expected)
        trailing_text = []
        # standard trailing text
        trailing_text.append(('m/s', 'm/s'))
        # unicode trailing text
        trailing_text.append((u'\xc3', u'\xc3'))
        # html escaped trailing text
        # this is the only one we expect to change
        trailing_text.append(('a &lt; b', 'a < b'))

        for xml_text, expected_text in trailing_text:
            xml_str = u"""<textline id="prob_1_2"
                            size="{size}"
                            trailing_text="{tt}"
                            />""".format(size=size, tt=xml_text)

            element = etree.fromstring(xml_str)

            state = {
                'value': 'BumbleBee',
                'response_data': RESPONSE_DATA
            }
            the_input = lookup_tag('textline')(test_capa_system(), element, state)

            context = the_input._get_render_context()  # pylint: disable=protected-access
            prob_id = 'prob_1_2'
            expected = {
                'STATIC_URL': '/dummy-static/',
                'id': prob_id,
                'value': 'BumbleBee',
                'status': inputtypes.Status('unanswered'),
                'size': size,
                'msg': '',
                'hidden': False,
                'inline': False,
                'do_math': False,
                'trailing_text': expected_text,
                'preprocessor': None,
                'response_data': RESPONSE_DATA,
                'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
            }
            self.assertEqual(context, expected)


class FileSubmissionTest(unittest.TestCase):
    '''
    Check that file submission inputs work
    '''

    def test_rendering(self):
        allowed_files = "runme.py nooooo.rb ohai.java"
        required_files = "cookies.py"

        xml_str = """<filesubmission id="prob_1_2"
        allowed_files="{af}"
        required_files="{rf}"
        />""".format(af=allowed_files,
                     rf=required_files,)

        element = etree.fromstring(xml_str)

        state = {
            'value': 'BumbleBee.py',
            'status': 'incomplete',
            'feedback': {'message': '3'},
            'response_data': RESPONSE_DATA
        }
        input_class = lookup_tag('filesubmission')
        the_input = input_class(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'status': inputtypes.Status('queued'),
            'msg': the_input.submitted_msg,
            'value': 'BumbleBee.py',
            'queue_len': '3',
            'allowed_files': '["runme.py", "nooooo.rb", "ohai.java"]',
            'required_files': '["cookies.py"]',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)


class CodeInputTest(unittest.TestCase):
    '''
    Check that codeinput inputs work
    '''

    def test_rendering(self):
        mode = "parrot"
        linenumbers = 'false'
        rows = '37'
        cols = '11'
        tabsize = '7'

        xml_str = """<codeinput id="prob_1_2"
        mode="{m}"
        cols="{c}"
        rows="{r}"
        linenumbers="{ln}"
        tabsize="{ts}"
        />""".format(m=mode, c=cols, r=rows, ln=linenumbers, ts=tabsize)

        element = etree.fromstring(xml_str)

        escapedict = {'"': '&quot;'}

        state = {
            'value': 'print "good evening"',
            'status': 'incomplete',
            'feedback': {'message': '3'},
            'response_data': RESPONSE_DATA
        }

        input_class = lookup_tag('codeinput')
        the_input = input_class(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'print "good evening"',
            'status': inputtypes.Status('queued'),
            'msg': the_input.submitted_msg,
            'mode': mode,
            'linenumbers': linenumbers,
            'rows': rows,
            'cols': cols,
            'hidden': '',
            'tabsize': int(tabsize),
            'queue_len': '3',
            'aria_label': '{mode} editor'.format(mode=mode),
            'code_mirror_exit_message': 'Press ESC then TAB or click outside of the code editor to exit',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)


class MatlabTest(unittest.TestCase):
    '''
    Test Matlab input types
    '''
    def setUp(self):
        super(MatlabTest, self).setUp()
        self.rows = '10'
        self.cols = '80'
        self.tabsize = '4'
        self.mode = ""
        self.payload = "payload"
        self.linenumbers = 'true'
        self.xml = """<matlabinput id="prob_1_2"
            rows="{r}" cols="{c}"
            tabsize="{tabsize}" mode="{m}"
            linenumbers="{ln}">
                <plot_payload>
                    {payload}
                </plot_payload>
            </matlabinput>""".format(r=self.rows,
                                     c=self.cols,
                                     tabsize=self.tabsize,
                                     m=self.mode,
                                     payload=self.payload,
                                     ln=self.linenumbers)
        elt = etree.fromstring(self.xml)
        state = {
            'value': 'print "good evening"',
            'status': 'incomplete',
            'feedback': {'message': '3'},
            'response_data': {}
        }

        self.input_class = lookup_tag('matlabinput')
        self.the_input = self.input_class(test_capa_system(), elt, state)

    def test_rendering(self):
        context = self.the_input._get_render_context()  # pylint: disable=protected-access

        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': 'prob_1_2',
            'value': 'print "good evening"',
            'status': inputtypes.Status('queued'),
            'msg': self.the_input.submitted_msg,
            'mode': self.mode,
            'rows': self.rows,
            'cols': self.cols,
            'queue_msg': '',
            'linenumbers': 'true',
            'hidden': '',
            'tabsize': int(self.tabsize),
            'button_enabled': True,
            'queue_len': '3',
            'matlab_editor_js': '/dummy-static/js/vendor/CodeMirror/octave.js',
            'response_data': {},
            'describedby_html': HTML('aria-describedby="status_prob_1_2"')
        }

        self.assertEqual(context, expected)

    def test_rendering_with_state(self):
        state = {
            'value': 'print "good evening"',
            'status': 'incomplete',
            'input_state': {'queue_msg': 'message'},
            'feedback': {'message': '3'},
            'response_data': RESPONSE_DATA
        }
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'print "good evening"',
            'status': inputtypes.Status('queued'),
            'msg': the_input.submitted_msg,
            'mode': self.mode,
            'rows': self.rows,
            'cols': self.cols,
            'queue_msg': 'message',
            'linenumbers': 'true',
            'hidden': '',
            'tabsize': int(self.tabsize),
            'button_enabled': True,
            'queue_len': '3',
            'matlab_editor_js': '/dummy-static/js/vendor/CodeMirror/octave.js',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)

    def test_rendering_when_completed(self):
        for status in ['correct', 'incorrect']:
            state = {
                'value': 'print "good evening"',
                'status': status,
                'input_state': {},
                'response_data': RESPONSE_DATA
            }
            elt = etree.fromstring(self.xml)
            prob_id = 'prob_1_2'
            the_input = self.input_class(test_capa_system(), elt, state)
            context = the_input._get_render_context()  # pylint: disable=protected-access
            expected = {
                'STATIC_URL': '/dummy-static/',
                'id': prob_id,
                'value': 'print "good evening"',
                'status': inputtypes.Status(status),
                'msg': '',
                'mode': self.mode,
                'rows': self.rows,
                'cols': self.cols,
                'queue_msg': '',
                'linenumbers': 'true',
                'hidden': '',
                'tabsize': int(self.tabsize),
                'button_enabled': False,
                'queue_len': '0',
                'matlab_editor_js': '/dummy-static/js/vendor/CodeMirror/octave.js',
                'response_data': RESPONSE_DATA,
                'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
            }

            self.assertEqual(context, expected)

    @patch('capa.inputtypes.time.time', return_value=10)
    def test_rendering_while_queued(self, time):
        state = {
            'value': 'print "good evening"',
            'status': 'incomplete',
            'input_state': {'queuestate': 'queued', 'queuetime': 5},
            'response_data': RESPONSE_DATA
        }
        elt = etree.fromstring(self.xml)
        prob_id = 'prob_1_2'
        the_input = self.input_class(test_capa_system(), elt, state)
        context = the_input._get_render_context()  # pylint: disable=protected-access
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'print "good evening"',
            'status': inputtypes.Status('queued'),
            'msg': the_input.submitted_msg,
            'mode': self.mode,
            'rows': self.rows,
            'cols': self.cols,
            'queue_msg': '',
            'linenumbers': 'true',
            'hidden': '',
            'tabsize': int(self.tabsize),
            'button_enabled': True,
            'queue_len': '1',
            'matlab_editor_js': '/dummy-static/js/vendor/CodeMirror/octave.js',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)

    def test_plot_data(self):
        data = {'submission': 'x = 1234;'}
        response = self.the_input.handle_ajax("plot", data)

        test_capa_system().xqueue['interface'].send_to_queue.assert_called_with(header=ANY, body=ANY)

        self.assertTrue(response['success'])
        self.assertIsNotNone(self.the_input.input_state['queuekey'])
        self.assertEqual(self.the_input.input_state['queuestate'], 'queued')

    def test_plot_data_failure(self):
        data = {'submission': 'x = 1234;'}
        error_message = 'Error message!'
        test_capa_system().xqueue['interface'].send_to_queue.return_value = (1, error_message)
        response = self.the_input.handle_ajax("plot", data)
        self.assertFalse(response['success'])
        self.assertEqual(response['message'], error_message)
        self.assertNotIn('queuekey', self.the_input.input_state)
        self.assertNotIn('queuestate', self.the_input.input_state)

    @patch('capa.inputtypes.time.time', return_value=10)
    def test_ungraded_response_success(self, time):
        queuekey = 'abcd'
        input_state = {'queuekey': queuekey, 'queuestate': 'queued', 'queuetime': 5}
        state = {'value': 'print "good evening"',
                 'status': 'incomplete',
                 'input_state': input_state,
                 'feedback': {'message': '3'}, }
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        inner_msg = 'hello!'
        queue_msg = json.dumps({'msg': inner_msg})

        the_input.ungraded_response(queue_msg, queuekey)
        self.assertIsNone(input_state['queuekey'])
        self.assertIsNone(input_state['queuestate'])
        self.assertEqual(input_state['queue_msg'], inner_msg)

    @patch('capa.inputtypes.time.time', return_value=10)
    def test_ungraded_response_key_mismatch(self, time):
        queuekey = 'abcd'
        input_state = {'queuekey': queuekey, 'queuestate': 'queued', 'queuetime': 5}
        state = {'value': 'print "good evening"',
                 'status': 'incomplete',
                 'input_state': input_state,
                 'feedback': {'message': '3'}, }
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        inner_msg = 'hello!'
        queue_msg = json.dumps({'msg': inner_msg})

        the_input.ungraded_response(queue_msg, 'abc')
        self.assertEqual(input_state['queuekey'], queuekey)
        self.assertEqual(input_state['queuestate'], 'queued')
        self.assertNotIn('queue_msg', input_state)

    @patch('capa.inputtypes.time.time', return_value=20)
    def test_matlab_response_timeout_not_exceeded(self, time):

        state = {'input_state': {'queuestate': 'queued', 'queuetime': 5}}
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        self.assertEqual(the_input.status, 'queued')

    @patch('capa.inputtypes.time.time', return_value=45)
    def test_matlab_response_timeout_exceeded(self, time):

        state = {'input_state': {'queuestate': 'queued', 'queuetime': 5}}
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        self.assertEqual(the_input.status, 'unsubmitted')
        self.assertEqual(the_input.msg, 'No response from Xqueue within {} seconds. Aborted.'.format(XQUEUE_TIMEOUT))

    @patch('capa.inputtypes.time.time', return_value=20)
    def test_matlab_response_migration_of_queuetime(self, time):
        """
        Test if problem was saved before queuetime was introduced.
        """
        state = {'input_state': {'queuestate': 'queued'}}
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        self.assertEqual(the_input.status, 'unsubmitted')

    def test_matlab_api_key(self):
        """
        Test that api_key ends up in the xqueue payload
        """
        elt = etree.fromstring(self.xml)
        system = test_capa_system()
        system.matlab_api_key = 'test_api_key'
        the_input = lookup_tag('matlabinput')(system, elt, {})

        data = {'submission': 'x = 1234;'}
        response = the_input.handle_ajax("plot", data)

        body = system.xqueue['interface'].send_to_queue.call_args[1]['body']
        payload = json.loads(body)
        self.assertEqual('test_api_key', payload['token'])
        self.assertEqual('2', payload['endpoint_version'])

    def test_get_html(self):
        # usual output
        output = self.the_input.get_html()
        self.assertEqual(
            etree.tostring(output),
            textwrap.dedent("""
            <div>{\'status\': Status(\'queued\'), \'button_enabled\': True, \'rows\': \'10\', \'queue_len\': \'3\',
            \'mode\': \'\', \'tabsize\': 4, \'cols\': \'80\', \'STATIC_URL\': \'/dummy-static/\', \'linenumbers\':
            \'true\', \'queue_msg\': \'\', \'value\': \'print "good evening"\',
            \'msg\': u\'Submitted. As soon as a response is returned, this message will be replaced by that feedback.\',
            \'matlab_editor_js\': \'/dummy-static/js/vendor/CodeMirror/octave.js\',
            \'hidden\': \'\', \'id\': \'prob_1_2\',
            \'describedby_html\': Markup(u\'aria-describedby="status_prob_1_2"\'), \'response_data\': {}}</div>
            """).replace('\n', ' ').strip()
        )

        # test html, that is correct HTML5 html, but is not parsable by XML parser.
        old_render_template = self.the_input.capa_system.render_template
        self.the_input.capa_system.render_template = lambda *args: textwrap.dedent("""
                <div class='matlabResponse'><div id='mwAudioPlaceHolder'>
                <audio controls autobuffer autoplay src='data:audio/wav;base64='>Audio is not supported on this browser.</audio>
                <div>Right click <a href=https://endpoint.mss-mathworks.com/media/filename.wav>here</a> and click \"Save As\" to download the file</div></div>
                <div style='white-space:pre' class='commandWindowOutput'></div><ul></ul></div>
            """).replace('\n', '')
        output = self.the_input.get_html()
        self.assertEqual(
            etree.tostring(output),
            textwrap.dedent("""
            <div class='matlabResponse'><div id='mwAudioPlaceHolder'>
            <audio src='data:audio/wav;base64=' autobuffer="" controls="" autoplay="">Audio is not supported on this browser.</audio>
            <div>Right click <a href="https://endpoint.mss-mathworks.com/media/filename.wav">here</a> and click \"Save As\" to download the file</div></div>
            <div style='white-space:pre' class='commandWindowOutput'/><ul/></div>
            """).replace('\n', '').replace('\'', '\"')
        )

        # check that exception is raised during parsing for html.
        self.the_input.capa_system.render_template = lambda *args: "<aaa"
        with self.assertRaises(etree.XMLSyntaxError):
            self.the_input.get_html()

        self.the_input.capa_system.render_template = old_render_template

    def test_malformed_queue_msg(self):
        # an actual malformed response
        queue_msg = textwrap.dedent("""
    <div class='matlabResponse'><div style='white-space:pre' class='commandWindowOutput'> <strong>if</strong> Conditionally execute statements.
    The general form of the <strong>if</strong> statement is

       <strong>if</strong> expression
         statements
       ELSEIF expression
         statements
       ELSE
         statements
       END

    The statements are executed if the real part of the expression
    has all non-zero elements. The ELSE and ELSEIF parts are optional.
    Zero or more ELSEIF parts can be used as well as nested <strong>if</strong>'s.
    The expression is usually of the form expr rop expr where
    rop is ==, <, >, <=, >=, or ~=.
    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAjAAAAGkCAIAAACgj==" />

    Example
       if I == J
         A(I,J) = 2;
       elseif abs(I-J) == 1
         A(I,J) = -1;
       else
         A(I,J) = 0;
       end

    See also <a href="matlab:help relop">relop</a>, <a href="matlab:help else">else</a>, <a href="matlab:help elseif">elseif</a>, <a href="matlab:help end">end</a>, <a href="matlab:help for">for</a>, <a href="matlab:help while">while</a>, <a href="matlab:help switch">switch</a>.

    Reference page in Help browser
       <a href="matlab:doc if">doc if</a>

    </div><ul></ul></div>
        """)

        state = {
            'value': 'print "good evening"',
            'status': 'incomplete',
            'input_state': {'queue_msg': queue_msg},
            'feedback': {'message': '3'},
            'response_data': RESPONSE_DATA
        }
        elt = etree.fromstring(self.xml)

        the_input = self.input_class(test_capa_system(), elt, state)
        context = the_input._get_render_context()  # pylint: disable=protected-access
        self.maxDiff = None
        expected = fromstring(u'\n<div class="matlabResponse"><div class="commandWindowOutput" style="white-space: pre;"> <strong>if</strong> Conditionally execute statements.\nThe general form of the <strong>if</strong> statement is\n\n   <strong>if</strong> expression\n     statements\n   ELSEIF expression\n     statements\n   ELSE\n     statements\n   END\n\nThe statements are executed if the real part of the expression \nhas all non-zero elements. The ELSE and ELSEIF parts are optional.\nZero or more ELSEIF parts can be used as well as nested <strong>if</strong>\'s.\nThe expression is usually of the form expr rop expr where \nrop is ==, &lt;, &gt;, &lt;=, &gt;=, or ~=.\n<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAjAAAAGkCAIAAACgj==">\n\nExample\n   if I == J\n     A(I,J) = 2;\n   elseif abs(I-J) == 1\n     A(I,J) = -1;\n   else\n     A(I,J) = 0;\n   end\n\nSee also <a>relop</a>, <a>else</a>, <a>elseif</a>, <a>end</a>, <a>for</a>, <a>while</a>, <a>switch</a>.\n\nReference page in Help browser\n   <a>doc if</a>\n\n</div><ul></ul></div>\n')
        received = fromstring(context['queue_msg'])
        html_tree_equal(received, expected)

    def test_rendering_with_invalid_queue_msg(self):
        self.the_input.queue_msg = (u"<div class='matlabResponse'><div style='white-space:pre' class='commandWindowOutput'>"
                                    u"\nans =\n\n\u0002\n\n</div><ul></ul></div>")
        context = self.the_input._get_render_context()  # pylint: disable=protected-access

        self.maxDiff = None
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'print "good evening"',
            'status': inputtypes.Status('queued'),
            'msg': self.the_input.submitted_msg,
            'mode': self.mode,
            'rows': self.rows,
            'cols': self.cols,
            'queue_msg': "<span>Error running code.</span>",
            'linenumbers': 'true',
            'hidden': '',
            'tabsize': int(self.tabsize),
            'button_enabled': True,
            'queue_len': '3',
            'matlab_editor_js': '/dummy-static/js/vendor/CodeMirror/octave.js',
            'response_data': {},
            'describedby_html': 'aria-describedby="status_{id}"'.format(id=prob_id)
        }

        self.assertEqual(context, expected)
        self.the_input.capa_system.render_template = DemoSystem().render_template
        self.the_input.get_html()  # Should not raise an exception

    def test_matlab_queue_message_allowed_tags(self):
        """
        Test allowed tags.
        """
        allowed_tags = ['div', 'p', 'audio', 'pre', 'span']
        for tag in allowed_tags:
            queue_msg = "<{0}>Test message</{0}>".format(tag)
            state = {
                'input_state': {'queue_msg': queue_msg},
                'status': 'queued',
            }
            elt = etree.fromstring(self.xml)
            the_input = self.input_class(test_capa_system(), elt, state)
            self.assertEqual(the_input.queue_msg, queue_msg)

    def test_matlab_queue_message_not_allowed_tag(self):
        """
        Test not allowed tag.
        """
        not_allowed_tag = 'script'
        queue_msg = "<{0}>Test message</{0}>".format(not_allowed_tag)
        state = {
            'input_state': {'queue_msg': queue_msg},
            'status': 'queued',
        }
        elt = etree.fromstring(self.xml)
        the_input = self.input_class(test_capa_system(), elt, state)
        expected = "&lt;script&gt;Test message&lt;/script&gt;"
        self.assertEqual(the_input.queue_msg, expected)

    def test_matlab_sanitize_msg(self):
        """
        Check that the_input.msg is sanitized.
        """
        not_allowed_tag = 'script'
        self.the_input.msg = "<{0}>Test message</{0}>".format(not_allowed_tag)
        expected = "&lt;script&gt;Test message&lt;/script&gt;"
        self.assertEqual(self.the_input._get_render_context()['msg'], expected)  # pylint: disable=protected-access


def html_tree_equal(received, expected):
    """
    Returns whether two etree Elements are the same, with insensitivity to attribute order.
    """
    for attr in ('tag', 'attrib', 'text', 'tail'):
        if getattr(received, attr) != getattr(expected, attr):
            return False
    if len(received) != len(expected):
        return False
    if any(not html_tree_equal(rec, exp) for rec, exp in zip(received, expected)):
        return False
    return True


class SchematicTest(unittest.TestCase):
    '''
    Check that schematic inputs work
    '''

    def test_rendering(self):
        height = '12'
        width = '33'
        parts = 'resistors, capacitors, and flowers'
        analyses = 'fast, slow, and pink'
        initial_value = 'two large batteries'
        submit_analyses = 'maybe'

        xml_str = """<schematic id="prob_1_2"
        height="{h}"
        width="{w}"
        parts="{p}"
        analyses="{a}"
        initial_value="{iv}"
        submit_analyses="{sa}"
        />""".format(h=height, w=width, p=parts, a=analyses,
                     iv=initial_value, sa=submit_analyses)

        element = etree.fromstring(xml_str)

        value = 'three resistors and an oscilating pendulum'
        state = {
            'value': value,
            'status': 'unsubmitted',
            'response_data': RESPONSE_DATA
        }

        the_input = lookup_tag('schematic')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': value,
            'status': inputtypes.Status('unsubmitted'),
            'msg': '',
            'initial_value': initial_value,
            'width': width,
            'height': height,
            'parts': parts,
            'setup_script': '/dummy-static/js/capa/schematicinput.js',
            'analyses': analyses,
            'submit_analyses': submit_analyses,
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)


class ImageInputTest(unittest.TestCase):
    '''
    Check that image inputs work
    '''

    def check(self, value, egx, egy):
        height = '78'
        width = '427'
        src = 'http://www.edx.org/cowclicker.jpg'

        xml_str = """<imageinput id="prob_1_2"
        src="{s}"
        height="{h}"
        width="{w}"
        />""".format(s=src, h=height, w=width)

        element = etree.fromstring(xml_str)

        state = {
            'value': value,
            'status': 'unsubmitted',
            'response_data': RESPONSE_DATA
        }

        the_input = lookup_tag('imageinput')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': value,
            'status': inputtypes.Status('unsubmitted'),
            'width': width,
            'height': height,
            'src': src,
            'gx': egx,
            'gy': egy,
            'msg': '',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)

    def test_with_value(self):
        # Check that compensating for the dot size works properly.
        self.check('[50,40]', 35, 25)

    def test_without_value(self):
        self.check('', 0, 0)

    def test_corrupt_values(self):
        self.check('[12', 0, 0)
        self.check('[12, a]', 0, 0)
        self.check('[12 10]', 0, 0)
        self.check('[12]', 0, 0)
        self.check('[12 13 14]', 0, 0)


class CrystallographyTest(unittest.TestCase):
    '''
    Check that crystallography inputs work
    '''

    def test_rendering(self):
        height = '12'
        width = '33'

        xml_str = """<crystallography id="prob_1_2"
        height="{h}"
        width="{w}"
        />""".format(h=height, w=width)

        element = etree.fromstring(xml_str)

        value = 'abc'
        state = {
            'value': value,
            'status': 'unsubmitted',
            'response_data': RESPONSE_DATA
        }

        the_input = lookup_tag('crystallography')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': value,
            'status': inputtypes.Status('unsubmitted'),
            'msg': '',
            'width': width,
            'height': height,
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)


class VseprTest(unittest.TestCase):
    '''
    Check that vsepr inputs work
    '''

    def test_rendering(self):
        height = '12'
        width = '33'
        molecules = "H2O, C2O"
        geometries = "AX12,TK421"

        xml_str = """<vsepr id="prob_1_2"
        height="{h}"
        width="{w}"
        molecules="{m}"
        geometries="{g}"
        />""".format(h=height, w=width, m=molecules, g=geometries)

        element = etree.fromstring(xml_str)

        value = 'abc'
        state = {
            'value': value,
            'status': 'unsubmitted',
            'response_data': RESPONSE_DATA
        }

        the_input = lookup_tag('vsepr_input')(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': value,
            'status': inputtypes.Status('unsubmitted'),
            'msg': '',
            'width': width,
            'height': height,
            'molecules': molecules,
            'geometries': geometries,
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.assertEqual(context, expected)


class ChemicalEquationTest(unittest.TestCase):
    '''
    Check that chemical equation inputs work.
    '''
    def setUp(self):
        super(ChemicalEquationTest, self).setUp()
        self.size = "42"
        xml_str = """<chemicalequationinput id="prob_1_2" size="{size}"/>""".format(size=self.size)

        element = etree.fromstring(xml_str)

        state = {
            'value': 'H2OYeah',
            'response_data': RESPONSE_DATA
        }
        self.the_input = lookup_tag('chemicalequationinput')(test_capa_system(), element, state)

    def test_rendering(self):
        ''' Verify that the render context matches the expected render context'''
        context = self.the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'H2OYeah',
            'status': inputtypes.Status('unanswered'),
            'msg': '',
            'size': self.size,
            'previewer': '/dummy-static/js/capa/chemical_equation_preview.js',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }
        self.assertEqual(context, expected)

    def test_chemcalc_ajax_sucess(self):
        ''' Verify that using the correct dispatch and valid data produces a valid response'''
        data = {'formula': "H"}
        response = self.the_input.handle_ajax("preview_chemcalc", data)

        self.assertIn('preview', response)
        self.assertNotEqual(response['preview'], '')
        self.assertEqual(response['error'], "")

    def test_ajax_bad_method(self):
        """
        With a bad dispatch, we shouldn't receive anything
        """
        response = self.the_input.handle_ajax("obviously_not_real", {})
        self.assertEqual(response, {})

    def test_ajax_no_formula(self):
        """
        When we ask for a formula rendering, there should be an error if no formula
        """
        response = self.the_input.handle_ajax("preview_chemcalc", {})
        self.assertIn('error', response)
        self.assertEqual(response['error'], "No formula specified.")

    def test_ajax_parse_err(self):
        """
        With parse errors, ChemicalEquationInput should give an error message
        """
        # Simulate answering a problem that raises the exception
        with patch('capa.inputtypes.chemcalc.render_to_html') as mock_render:
            mock_render.side_effect = ParseException(u"ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ")
            response = self.the_input.handle_ajax(
                "preview_chemcalc",
                {'formula': 'H2O + invalid chemistry'}
            )

        self.assertIn('error', response)
        self.assertIn("Couldn't parse formula", response['error'])

    @patch('capa.inputtypes.log')
    def test_ajax_other_err(self, mock_log):
        """
        With other errors, test that ChemicalEquationInput also logs it
        """
        with patch('capa.inputtypes.chemcalc.render_to_html') as mock_render:
            mock_render.side_effect = Exception()
            response = self.the_input.handle_ajax(
                "preview_chemcalc",
                {'formula': 'H2O + superterrible chemistry'}
            )
        mock_log.warning.assert_called_once_with(
            "Error while previewing chemical formula", exc_info=True
        )
        self.assertIn('error', response)
        self.assertEqual(response['error'], "Error while rendering preview")


class FormulaEquationTest(unittest.TestCase):
    """
    Check that formula equation inputs work.
    """
    def setUp(self):
        super(FormulaEquationTest, self).setUp()
        self.size = "42"
        xml_str = """<formulaequationinput id="prob_1_2" size="{size}"/>""".format(size=self.size)

        element = etree.fromstring(xml_str)

        state = {
            'value': 'x^2+1/2',
            'response_data': RESPONSE_DATA
        }
        self.the_input = lookup_tag('formulaequationinput')(test_capa_system(), element, state)

    def test_rendering(self):
        """
        Verify that the render context matches the expected render context
        """
        context = self.the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'prob_1_2'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': 'x^2+1/2',
            'status': inputtypes.Status('unanswered'),
            'msg': '',
            'size': self.size,
            'previewer': '/dummy-static/js/capa/src/formula_equation_preview.js',
            'inline': False,
            'trailing_text': '',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }
        self.assertEqual(context, expected)

    def test_trailing_text_rendering(self):
        """
        Verify that the render context matches the expected render context with trailing_text
        """
        size = "42"
        # store (xml_text, expected)
        trailing_text = []
        # standard trailing text
        trailing_text.append(('m/s', 'm/s'))
        # unicode trailing text
        trailing_text.append((u'\xc3', u'\xc3'))
        # html escaped trailing text
        # this is the only one we expect to change
        trailing_text.append(('a &lt; b', 'a < b'))

        for xml_text, expected_text in trailing_text:
            xml_str = u"""<formulaequationinput id="prob_1_2"
                            size="{size}"
                            trailing_text="{tt}"
                            />""".format(size=size, tt=xml_text)

            element = etree.fromstring(xml_str)

            state = {
                'value': 'x^2+1/2',
                'response_data': RESPONSE_DATA
            }
            the_input = lookup_tag('formulaequationinput')(test_capa_system(), element, state)

            context = the_input._get_render_context()  # pylint: disable=protected-access
            prob_id = 'prob_1_2'
            expected = {
                'STATIC_URL': '/dummy-static/',
                'id': prob_id,
                'value': 'x^2+1/2',
                'status': inputtypes.Status('unanswered'),
                'msg': '',
                'size': size,
                'previewer': '/dummy-static/js/capa/src/formula_equation_preview.js',
                'inline': False,
                'trailing_text': expected_text,
                'response_data': RESPONSE_DATA,
                'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
            }

            self.assertEqual(context, expected)

    def test_formcalc_ajax_sucess(self):
        """
        Verify that using the correct dispatch and valid data produces a valid response
        """
        data = {'formula': "x^2+1/2", 'request_start': 0}
        response = self.the_input.handle_ajax("preview_formcalc", data)

        self.assertIn('preview', response)
        self.assertNotEqual(response['preview'], '')
        self.assertEqual(response['error'], "")
        self.assertEqual(response['request_start'], data['request_start'])

    def test_ajax_bad_method(self):
        """
        With a bad dispatch, we shouldn't receive anything
        """
        response = self.the_input.handle_ajax("obviously_not_real", {})
        self.assertEqual(response, {})

    def test_ajax_no_formula(self):
        """
        When we ask for a formula rendering, there should be an error if no formula
        """
        response = self.the_input.handle_ajax(
            "preview_formcalc",
            {'request_start': 1, }
        )
        self.assertIn('error', response)
        self.assertEqual(response['error'], "No formula specified.")

    def test_ajax_parse_err(self):
        """
        With parse errors, FormulaEquationInput should give an error message
        """
        # Simulate answering a problem that raises the exception
        with patch('capa.inputtypes.latex_preview') as mock_preview:
            mock_preview.side_effect = ParseException("Oopsie")
            response = self.the_input.handle_ajax(
                "preview_formcalc",
                {'formula': 'x^2+1/2', 'request_start': 1, }
            )

        self.assertIn('error', response)
        self.assertEqual(response['error'], "Sorry, couldn't parse formula")

    @patch('capa.inputtypes.log')
    def test_ajax_other_err(self, mock_log):
        """
        With other errors, test that FormulaEquationInput also logs it
        """
        with patch('capa.inputtypes.latex_preview') as mock_preview:
            mock_preview.side_effect = Exception()
            response = self.the_input.handle_ajax(
                "preview_formcalc",
                {'formula': 'x^2+1/2', 'request_start': 1, }
            )
        mock_log.warning.assert_called_once_with(
            "Error while previewing formula", exc_info=True
        )
        self.assertIn('error', response)
        self.assertEqual(response['error'], "Error while rendering preview")


class DragAndDropTest(unittest.TestCase):
    '''
    Check that drag and drop inputs work
    '''

    def test_rendering(self):
        path_to_images = '/dummy-static/images/'

        xml_str = """
        <drag_and_drop_input id="prob_1_2" img="{path}about_1.png" target_outline="false">
            <draggable id="1" label="Label 1"/>
            <draggable id="name_with_icon" label="cc" icon="{path}cc.jpg"/>
            <draggable id="with_icon" label="arrow-left" icon="{path}arrow-left.png" />
            <draggable id="5" label="Label2" />
            <draggable id="2" label="Mute" icon="{path}mute.png" />
            <draggable id="name_label_icon3" label="spinner" icon="{path}spinner.gif" />
            <draggable id="name4" label="Star" icon="{path}volume.png" />
            <draggable id="7" label="Label3" />

            <target id="t1" x="210" y="90" w="90" h="90"/>
            <target id="t2" x="370" y="160" w="90" h="90"/>

        </drag_and_drop_input>
        """.format(path=path_to_images)

        element = etree.fromstring(xml_str)

        value = 'abc'
        state = {
            'value': value,
            'status': 'unsubmitted',
            'response_data': RESPONSE_DATA
        }

        user_input = {  # order matters, for string comparison
                        "target_outline": "false",
                        "base_image": "/dummy-static/images/about_1.png",
                        "draggables": [
                            {"can_reuse": "", "label": "Label 1", "id": "1", "icon": "", "target_fields": []},
                            {"can_reuse": "", "label": "cc", "id": "name_with_icon", "icon": "/dummy-static/images/cc.jpg", "target_fields": []},
                            {"can_reuse": "", "label": "arrow-left", "id": "with_icon", "icon": "/dummy-static/images/arrow-left.png", "target_fields": []},
                            {"can_reuse": "", "label": "Label2", "id": "5", "icon": "", "target_fields": []},
                            {"can_reuse": "", "label": "Mute", "id": "2", "icon": "/dummy-static/images/mute.png", "target_fields": []},
                            {"can_reuse": "", "label": "spinner", "id": "name_label_icon3", "icon": "/dummy-static/images/spinner.gif", "target_fields": []},
                            {"can_reuse": "", "label": "Star", "id": "name4", "icon": "/dummy-static/images/volume.png", "target_fields": []},
                            {"can_reuse": "", "label": "Label3", "id": "7", "icon": "", "target_fields": []}],
                        "one_per_target": "True",
                        "targets": [
                            {"y": "90", "x": "210", "id": "t1", "w": "90", "h": "90"},
                            {"y": "160", "x": "370", "id": "t2", "w": "90", "h": "90"}
                        ]
        }

        the_input = lookup_tag('drag_and_drop_input')(test_capa_system(), element, state)
        prob_id = 'prob_1_2'
        context = the_input._get_render_context()  # pylint: disable=protected-access
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'value': value,
            'status': inputtypes.Status('unsubmitted'),
            'msg': '',
            'drag_and_drop_json': json.dumps(user_input),
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        # as we are dumping 'draggables' dicts while dumping user_input, string
        # comparison will fail, as order of keys is random.
        self.assertEqual(json.loads(context['drag_and_drop_json']), user_input)
        context.pop('drag_and_drop_json')
        expected.pop('drag_and_drop_json')
        self.assertEqual(context, expected)


class AnnotationInputTest(unittest.TestCase):
    '''
    Make sure option inputs work
    '''
    def test_rendering(self):
        xml_str = '''
<annotationinput>
    <title>foo</title>
    <text>bar</text>
    <comment>my comment</comment>
    <comment_prompt>type a commentary</comment_prompt>
    <tag_prompt>select a tag</tag_prompt>
    <options>
        <option choice="correct">x</option>
        <option choice="incorrect">y</option>
        <option choice="partially-correct">z</option>
    </options>
</annotationinput>
'''
        element = etree.fromstring(xml_str)

        value = {"comment": "blah blah", "options": [1]}
        json_value = json.dumps(value)
        state = {
            'value': json_value,
            'id': 'annotation_input',
            'status': 'answered',
            'response_data': RESPONSE_DATA
        }

        tag = 'annotationinput'

        the_input = lookup_tag(tag)(test_capa_system(), element, state)

        context = the_input._get_render_context()  # pylint: disable=protected-access
        prob_id = 'annotation_input'
        expected = {
            'STATIC_URL': '/dummy-static/',
            'id': prob_id,
            'status': inputtypes.Status('answered'),
            'msg': '',
            'title': 'foo',
            'text': 'bar',
            'comment': 'my comment',
            'comment_prompt': 'type a commentary',
            'tag_prompt': 'select a tag',
            'options': [
                {'id': 0, 'description': 'x', 'choice': 'correct'},
                {'id': 1, 'description': 'y', 'choice': 'incorrect'},
                {'id': 2, 'description': 'z', 'choice': 'partially-correct'}
            ],
            'value': json_value,
            'options_value': value['options'],
            'has_options_value': len(value['options']) > 0,
            'comment_value': value['comment'],
            'debug': False,
            'return_to_annotation': True,
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }

        self.maxDiff = None
        self.assertDictEqual(context, expected)


class TestChoiceText(unittest.TestCase):
    """
    Tests for checkboxtextgroup inputs
    """
    @staticmethod
    def build_choice_element(node_type, contents, tail_text, value):
        """
        Builds a content node for a choice.
        """
        # When xml is being parsed numtolerance_input and decoy_input tags map to textinput type
        # in order to provide the template with correct rendering information.
        if node_type in ('numtolerance_input', 'decoy_input'):
            node_type = 'textinput'
        choice = {'type': node_type, 'contents': contents, 'tail_text': tail_text, 'value': value}
        return choice

    def check_group(self, tag, choice_tag, expected_input_type):
        """
        Build a radio or checkbox group, parse it and check the resuls against the
        expected output.

        `tag` should be 'checkboxtextgroup' or 'radiotextgroup'
        `choice_tag` is either 'choice' for proper xml, or any other value to trigger an error.
        `expected_input_type` is either 'radio' or 'checkbox'.
        """
        xml_str = """
  <{tag}>
      <{choice_tag} correct="false" name="choiceinput_0">this is<numtolerance_input name="choiceinput_0_textinput_0"/>false</{choice_tag}>
      <choice correct="true" name="choiceinput_1">Is a number<decoy_input name="choiceinput_1_textinput_0"/><text>!</text></choice>
  </{tag}>
        """.format(tag=tag, choice_tag=choice_tag)
        element = etree.fromstring(xml_str)
        prob_id = 'choicetext_input'
        state = {
            'value': '{}',
            'id': prob_id,
            'status': inputtypes.Status('answered'),
            'response_data': RESPONSE_DATA
        }

        first_input = self.build_choice_element('numtolerance_input', 'choiceinput_0_textinput_0', 'false', '')
        second_input = self.build_choice_element('decoy_input', 'choiceinput_1_textinput_0', '', '')
        first_choice_content = self.build_choice_element('text', 'this is', '', '')
        second_choice_content = self.build_choice_element('text', 'Is a number', '', '')
        second_choice_text = self.build_choice_element('text', "!", '', '')

        choices = [
            ('choiceinput_0', [first_choice_content, first_input]),
            ('choiceinput_1', [second_choice_content, second_input, second_choice_text])
        ]
        expected = {
            'STATIC_URL': '/dummy-static/',
            'msg': '',
            'input_type': expected_input_type,
            'choices': choices,
            'show_correctness': 'always',
            'submitted_message': 'Answer received.',
            'response_data': RESPONSE_DATA,
            'describedby_html': DESCRIBEDBY.format(status_id=prob_id)
        }
        expected.update(state)
        the_input = lookup_tag(tag)(test_capa_system(), element, state)
        context = the_input._get_render_context()  # pylint: disable=protected-access
        self.assertEqual(context, expected)

    def test_radiotextgroup(self):
        """
        Test that a properly formatted radiotextgroup problem generates
        expected ouputs
        """
        self.check_group('radiotextgroup', 'choice', 'radio')

    def test_checkboxtextgroup(self):
        """
        Test that a properly formatted checkboxtextgroup problem generates
        expected ouput
        """
        self.check_group('checkboxtextgroup', 'choice', 'checkbox')

    def test_invalid_tag(self):
        """
        Test to ensure that an unrecognized inputtype tag causes an error
        """
        with self.assertRaises(Exception):
            self.check_group('invalid', 'choice', 'checkbox')

    def test_invalid_input_tag(self):
        """
        Test to ensure having a tag other than <choice> inside of
        a checkbox or radiotextgroup problem raises an error.
        """
        with self.assertRaisesRegexp(Exception, "Error in xml"):
            self.check_group('checkboxtextgroup', 'invalid', 'checkbox')


class TestStatus(unittest.TestCase):
    """
    Tests for Status class
    """
    def test_str(self):
        """
        Test stringifing Status objects
        """
        statobj = inputtypes.Status('test')
        self.assertEqual(str(statobj), 'test')
        self.assertEqual(unicode(statobj), u'test')

    def test_classes(self):
        """
        Test that css classnames are correct
        """
        css_classes = [
            ('unsubmitted', 'unanswered'),
            ('incomplete', 'incorrect'),
            ('queued', 'processing'),
            ('correct', 'correct'),
            ('test', 'test'),
        ]
        for status, classname in css_classes:
            statobj = inputtypes.Status(status)
            self.assertEqual(statobj.classname, classname)

    def test_display_names(self):
        """
        Test that display names are correct
        """
        names = [
            ('correct', u'correct'),
            ('incorrect', u'incorrect'),
            ('incomplete', u'incomplete'),
            ('unanswered', u'unanswered'),
            ('unsubmitted', u'unanswered'),
            ('queued', u'processing'),
            ('dave', u'dave'),
        ]
        for status, display_name in names:
            statobj = inputtypes.Status(status)
            self.assertEqual(statobj.display_name, display_name)

    def test_translated_names(self):
        """
        Test that display names are "translated"
        """
        func = lambda t: t.upper()
        # status is in the mapping
        statobj = inputtypes.Status('queued', func)
        self.assertEqual(statobj.display_name, u'PROCESSING')

        # status is not in the mapping
        statobj = inputtypes.Status('test', func)
        self.assertEqual(statobj.display_name, u'test')
        self.assertEqual(str(statobj), 'test')
        self.assertEqual(statobj.classname, 'test')
