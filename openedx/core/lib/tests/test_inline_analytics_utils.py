"""
Inline analytics utility tests
"""

import unittest
import textwrap

from django.conf import settings
from django.test.utils import override_settings

from xmodule.tests.test_capa_module import CapaFactory

from openedx.core.lib.inline_analytics_utils import get_responses_data


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Run only in LMS')
class ResponseTest(unittest.TestCase):
    """ unittest class """

    def setUp(self):
        super(ResponseTest, self).setUp()
        self.module = CapaFactory.create()

    def test_capa_module(self):

        response = get_responses_data(self.module)
        self.assertEquals(len(response), 1)

    @override_settings(INLINE_ANALYTICS_SUPPORTED_TYPES={})
    def test_no_valid_types(self):

        response = get_responses_data(self.module)
        self.assertEquals(response, [])

    def test_invalid_type(self):

        response = get_responses_data('invalid_type')
        self.assertEquals(response, [])

    def test_rerandomize_true(self):

        module = CapaFactory.create(rerandomize='always')
        response = get_responses_data(module)
        self.assertEquals(response[0].message,
                          'The analytics cannot be displayed for this question as it uses randomization.')

    @override_settings(INLINE_ANALYTICS_SUPPORTED_TYPES={'DummyType': 'dummy'})
    def test_other_type(self):

        response = get_responses_data(self.module)
        self.assertEquals(response[0].message, 'The analytics cannot be displayed for this type of question.')

    def test_multi_responses(self):

        xml = textwrap.dedent("""\
        <?xml version="1.0"?>
        <problem>
        <p>1st question</p>
        <choiceresponse>
            <checkboxgroup direction="vertical">
                <choice correct="true">row 1</choice>
                <choice correct="true">row 2</choice>
                <choice correct="false">row 3</choice>
            </checkboxgroup>
        </choiceresponse>
        <p>2nd question in the same problem:</p>
        <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
                <choice correct="false">1st choice text</choice>
                <choice correct="false">2nd choice text</choice>
                <choice correct="true">3rd choice text</choice>
            </choicegroup>
        </multiplechoiceresponse>
        </problem>
        """)

        module = CapaFactory.create(xml=xml)
        response = get_responses_data(module)

        self.assertEquals(response[0].correct_response, ['choice_0', 'choice_1'])
        self.assertEquals(response[1].correct_response, ['choice_2'])
        self.assertEquals(response[0].response_type, 'checkbox')
        self.assertEquals(response[1].response_type, 'radio')
        self.assertEquals(response[0].message, None)
        self.assertEquals(response[1].message, None)
        self.assertEquals(response[0].choice_name_list, '[]')
        self.assertEquals(response[1].choice_name_list,
                          '[&quot;choice_0&quot;, &quot;choice_1&quot;, &quot;choice_2&quot;]')

    def test_multi_responses_name_mask(self):

        xml = textwrap.dedent("""\
        <?xml version="1.0"?>
        <problem>
        <p>1st question</p>
        <choiceresponse>
            <checkboxgroup direction="vertical">
                <choice correct="true">row 1</choice>
                <choice correct="true">row 2</choice>
                <choice correct="false">row 3</choice>
            </checkboxgroup>
        </choiceresponse>
        <p>2nd question in the same problem:</p>
        <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
                <choice correct="false" name="Tom">1st choice text</choice>
                <choice correct="false" name="Dick">2nd choice text</choice>
                <choice correct="true" name="Harry">3rd choice text</choice>
            </choicegroup>
        </multiplechoiceresponse>
        </problem>
        """)

        module = CapaFactory.create(xml=xml)
        response = get_responses_data(module)

        self.assertEquals(response[0].correct_response, ['choice_0', 'choice_1'])
        self.assertEquals(response[1].correct_response, ['choice_Harry'])
        self.assertEquals(response[0].response_type, 'checkbox')
        self.assertEquals(response[1].response_type, 'radio')
        self.assertEquals(response[0].message, None)
        self.assertEquals(response[1].message, None)
        self.assertEquals(response[0].choice_name_list, '[]')
        self.assertEquals(response[1].choice_name_list,
                          '[&quot;choice_Tom&quot;, &quot;choice_Dick&quot;, &quot;choice_Harry&quot;]')
