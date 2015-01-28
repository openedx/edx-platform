from datetime import datetime
import json
import unittest
from mock import Mock, MagicMock
from webob.multidict import MultiDict
from pytz import UTC
from xblock.fields import ScopeIds
from xmodule.open_ended_grading_classes.self_assessment_module import SelfAssessmentModule
from opaque_keys.edx.locations import Location
from lxml import etree

from . import get_test_system

import test_util_open_ended


class SelfAssessmentTest(unittest.TestCase):
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric></rubric>'''

    prompt = etree.XML("<prompt>This is sample prompt text.</prompt>")
    definition = {
        'rubric': rubric,
        'prompt': prompt,
        'submitmessage': 'Shall we submit now?',
        'hintprompt': 'Consider this...',
    }

    location = Location("edX", "sa_test", "run", "selfassessment", "SampleQuestion", None)

    descriptor = Mock()

    def setUp(self):
        super(SelfAssessmentTest, self).setUp()

        self.static_data = {
            'max_attempts': 10,
            'rubric': etree.XML(self.rubric),
            'prompt': self.prompt,
            'max_score': 1,
            'display_name': "Name",
            'accept_file_upload': False,
            'close_date': None,
            's3_interface': test_util_open_ended.S3_INTERFACE,
            'open_ended_grading_interface': test_util_open_ended.OPEN_ENDED_GRADING_INTERFACE,
            'skip_basic_checks': False,
            'control': {
                'required_peer_grading': 1,
                'peer_grader_count': 1,
                'min_to_calibrate': 3,
                'max_to_calibrate': 6,
                'peer_grade_finished_submissions_when_none_pending': False,
            }
        }

        system = get_test_system()

        usage_key = system.course_id.make_usage_key('combinedopenended', 'test_loc')
        scope_ids = ScopeIds(1, 'combinedopenended', usage_key, usage_key)
        system.xmodule_instance = Mock(scope_ids=scope_ids)
        self.module = SelfAssessmentModule(
            system,
            self.location,
            self.definition,
            self.descriptor,
            self.static_data
        )

    def test_get_html(self):
        html = self.module.get_html(self.module.system)
        self.assertTrue("This is sample prompt text" in html)

    def test_self_assessment_flow(self):
        responses = {'assessment': '0', 'score_list[]': ['0', '0']}

        def get_fake_item(name):
            return responses[name]

        def get_data_for_location(self, location, student):
            return {
                'count_graded': 0,
                'count_required': 0,
                'student_sub_count': 0,
            }

        mock_query_dict = MagicMock()
        mock_query_dict.__getitem__.side_effect = get_fake_item
        mock_query_dict.getall = get_fake_item

        self.module.peer_gs.get_data_for_location = get_data_for_location

        self.assertEqual(self.module.get_score()['score'], 0)

        self.module.save_answer({'student_answer': "I am an answer"},
                                self.module.system)
        self.assertEqual(self.module.child_state, self.module.ASSESSING)

        self.module.save_assessment(mock_query_dict, self.module.system)
        self.assertEqual(self.module.child_state, self.module.DONE)

        d = self.module.reset({})
        self.assertTrue(d['success'])
        self.assertEqual(self.module.child_state, self.module.INITIAL)

        # if we now assess as right, skip the REQUEST_HINT state
        self.module.save_answer({'student_answer': 'answer 4'},
                                self.module.system)
        responses['assessment'] = '1'
        self.module.save_assessment(mock_query_dict, self.module.system)
        self.assertEqual(self.module.child_state, self.module.DONE)

    def test_self_assessment_display(self):
        """
        Test storing an answer with the self assessment module.
        """

        # Create a module with no state yet.  Important that this start off as a blank slate.
        test_module = SelfAssessmentModule(
            get_test_system(),
            self.location,
            self.definition,
            self.descriptor,
            self.static_data
        )

        saved_response = "Saved response."
        submitted_response = "Submitted response."

        # Initially, there will be no stored answer.
        self.assertEqual(test_module.stored_answer, None)
        # And the initial answer to display will be an empty string.
        self.assertEqual(test_module.get_display_answer(), "")

        # Now, store an answer in the module.
        test_module.handle_ajax("store_answer", {'student_answer': saved_response}, get_test_system())
        # The stored answer should now equal our response.
        self.assertEqual(test_module.stored_answer, saved_response)
        self.assertEqual(test_module.get_display_answer(), saved_response)

        # Submit a student response to the question.
        test_module.handle_ajax("save_answer", {"student_answer": submitted_response}, get_test_system())
        # Submitting an answer should clear the stored answer.
        self.assertEqual(test_module.stored_answer, None)
        # Confirm that the answer is stored properly.
        self.assertEqual(test_module.latest_answer(), submitted_response)

        # Mock saving an assessment.
        assessment_dict = MultiDict({'assessment': 0, 'score_list[]': 0})
        data = test_module.handle_ajax("save_assessment", assessment_dict, get_test_system())
        self.assertTrue(json.loads(data)['success'])

        # Reset the module so the student can try again.
        test_module.reset(get_test_system())

        # Confirm that the right response is loaded.
        self.assertEqual(test_module.get_display_answer(), submitted_response)

    def test_save_assessment_after_closing(self):
        """
        Test storing assessment when close date is passed.
        """

        responses = {'assessment': '0', 'score_list[]': ['0', '0']}

        self.module.save_answer({'student_answer': "I am an answer"}, self.module.system)
        self.assertEqual(self.module.child_state, self.module.ASSESSING)

        #Set close date to current datetime.
        self.module.close_date = datetime.now(UTC)

        #Save assessment when close date is passed.
        self.module.save_assessment(responses, self.module.system)
        self.assertNotEqual(self.module.child_state, self.module.DONE)
