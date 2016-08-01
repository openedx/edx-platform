"""
Test capa problem.
"""
import unittest

from . import new_loncapa_problem


class CAPAProblemTest(unittest.TestCase):
    """ CAPA problem related tests"""

    def test_label_and_description_inside_responsetype(self):
        """
        Verify that
        * label is extracted
        * description_ids are constructed
        * <label> tag is removed to avoid duplication

        This is the case when we have a problem with single question or
        problem with multiple-questions separated as per the new format.
        """
        xml = """
        <problem>
            <choiceresponse>
                <label>Select the correct synonym of paranoid?</label>
                <description>Only the paranoid survive.</description>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '1_description_2_1',
                    'label': 'Select the correct synonym of paranoid?',
                    'descriptions': {'1_description_2_1': 'Only the paranoid survive.'}
                }
            }
        )
        self.assertEqual(len(problem.tree.xpath('//label')), 0)

    def test_label_attribute_only(self):
        """
        Verify that label is extracted and <p> tag with question
        text is removed when label attribute is set on inputtype.
        """
        question = "Once we become predictable, we become ______?"
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <p>{}</p>
            <stringresponse answer="vulnerable" type="ci">
                <textline label="{}" size="40"/>
            </stringresponse>
        </problem>
        """.format(question, question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {'1_2': {'description_ids': '', 'label': question, 'descriptions': {}}}

        )
        self.assertEqual(
            len(problem.tree.xpath('//p[text()="{}"]'.format(question))),
            0
        )

    def test_neither_label_tag_nor_attribute(self):
        """
        Verify that label is extracted correctly.

        This is the case when we have a markdown problem with multiple-questions.
        In this case when markdown is converted to xml, there will be no label
        tag and label attribute inside responsetype. But we have a label tag
        before the responsetype.
        """
        question1 = 'People who say they have nothing to ____ almost always do?'
        question2 = 'Select the correct synonym of paranoid?'
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <label>{}</label>
            <stringresponse answer="hide" type="ci">
                <textline size="40"/>
            </stringresponse>
            <choiceresponse>
                <label>{}</label>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """.format(question1, question2)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '',
                    'label': question1,
                    'descriptions': {}
                },
                '1_3':
                {
                    'description_ids': '',
                    'label': question2,
                    'descriptions': {}
                }
            }

        )
        for question in (question1, question2):
            self.assertEqual(
                len(problem.tree.xpath('//label[text()="{}"]'.format(question))),
                0
            )

    def test_multiple_descriptions(self):
        """
        Verify that multiple descriptions are handled correctly.
        """
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <stringresponse answer="War" type="ci">
                <label>___ requires sacrifices.</label>
                <description>The problem with trying to be the bad guy, there's always someone worse.</description>
                <description>Anyone who looks the world as if it was a game of chess deserves to lose.</description>
                <textline size="40"/>
            </stringresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '1_description_2_1 1_description_2_2',
                    'label': '___ requires sacrifices.',
                    'descriptions': {
                        '1_description_2_1': "The problem with trying to be the bad guy, there's always someone worse.",
                        '1_description_2_2': "Anyone who looks the world as if it was a game of chess deserves to lose."
                    }
                }
            }
        )

    def test_default_question_text(self):
        """
        Verify that default question text is shown when question is missing.
        """
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <stringresponse answer="War" type="ci">
                <description>Everybody needs somebody to talk to.</description>
                <textline size="40"/>
            </stringresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '1_description_2_1',
                    'label': 'You must specify meaningful question text.',
                    'descriptions': {
                        '1_description_2_1': "Everybody needs somebody to talk to."
                    }
                }
            }
        )

    def test_question_is_not_removed(self):
        """
        Verify that tag with question text is not removed when responsetype is not fully accessible.
        """
        question = "Click the country which is home to the Pyramids."
        xml = """
        <problem>
            <p>{}</p>
            <imageresponse>
                <imageinput label="{}"
                src="/static/Africa.png" width="600" height="638" rectangle="(338,98)-(412,168)"/>
            </imageresponse>
        </problem>
        """.format(question, question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '',
                    'label': 'Click the country which is home to the Pyramids.',
                    'descriptions': {}
                }
            }
        )
        # <p> tag with question text should not be deleted
        self.assertEqual(problem.tree.xpath("string(p[text()='{}'])".format(question)), question)

    def test_label_is_empty_if_no_label_attribute(self):
        """
        Verify that label in response_data is empty string when label
        attribute is missing and responsetype is not fully accessible.
        """
        question = "Click the country which is home to the Pyramids."
        xml = """
        <problem>
            <p>{}</p>
            <imageresponse>
                <imageinput
                src="/static/Africa.png" width="600" height="638" rectangle="(338,98)-(412,168)"/>
            </imageresponse>
        </problem>
        """.format(question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '',
                    'label': '',
                    'descriptions': {}
                }
            }
        )

    def test_multiple_questions_problem(self):
        """
        For a problem with multiple questions verify that for each question
        * label is extracted
        * descriptions info is constructed
        * <label> tag is removed to avoid duplication
        """
        xml = """
        <problem>
            <choiceresponse>
                <label>Select the correct synonym of paranoid?</label>
                <description>Only the paranoid survive.</description>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
            <multiplechoiceresponse>
                <p>one more question</p>
                <label>What Apple device competed with the portable CD player?</label>
                <description>Device looks like an egg plant.</description>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">The iPad</choice>
                    <choice correct="false">Napster</choice>
                    <choice correct="true">The iPod</choice>
                    <choice correct="false">The vegetable peeler</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '1_description_2_1',
                    'label': 'Select the correct synonym of paranoid?',
                    'descriptions': {'1_description_2_1': 'Only the paranoid survive.'}
                },
                '1_3':
                {
                    'description_ids': '1_description_3_1',
                    'label': 'What Apple device competed with the portable CD player?',
                    'descriptions': {'1_description_3_1': 'Device looks like an egg plant.'}
                }
            }
        )
        self.assertEqual(len(problem.tree.xpath('//label')), 0)

    def test_label_attribute_mismatches_question_tag(self):
        """
        Verify that question text is extracted correctly when label attribtue value
        mismatched with question tag value.

        This is the case when author updated the question <p> tag directly in XML but
        didn't changed the label attribute value. In this case we will consider the
        first <p> tag before responsetype as question.
        """
        question = 'Select the correct synonym of paranoid?'
        xml = """
        <problem>
            <p>Choose wisely.</p>
            <p>{}</p>
            <choiceresponse>
                <checkboxgroup label="Is egg plant a fruit?">
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """.format(question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2':
                {
                    'description_ids': '',
                    'label': question,
                    'descriptions': {}
                }
            }
        )
        self.assertEqual(
            len(problem.tree.xpath('//p[text()="{}"]'.format(question))),
            0
        )
