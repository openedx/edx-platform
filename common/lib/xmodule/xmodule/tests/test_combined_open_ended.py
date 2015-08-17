"""
Tests for the various pieces of the CombinedOpenEndedGrading system

OpenEndedChild
OpenEndedModule

"""

import json
import logging
import unittest

from datetime import datetime
from lxml import etree
from lxml.html import fragment_fromstring
from mock import Mock, MagicMock, patch
from pytz import UTC
from webob.multidict import MultiDict

from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from xmodule.open_ended_grading_classes.open_ended_module import OpenEndedModule
from xmodule.open_ended_grading_classes.self_assessment_module import SelfAssessmentModule
from xmodule.open_ended_grading_classes.combined_open_ended_modulev1 import CombinedOpenEndedV1Module
from xmodule.combined_open_ended_module import CombinedOpenEndedModule
from opaque_keys.edx.locations import Location
from xmodule.tests import get_test_system, test_util_open_ended
from xmodule.progress import Progress
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import STUDENT_VIEW

from xmodule.tests.test_util_open_ended import (
    DummyModulestore, TEST_STATE_SA_IN,
    MOCK_INSTANCE_STATE, TEST_STATE_SA, TEST_STATE_AI, TEST_STATE_AI2, TEST_STATE_AI2_INVALID,
    TEST_STATE_SINGLE, TEST_STATE_PE_SINGLE, MockUploadedFile, INSTANCE_INCONSISTENT_STATE,
    INSTANCE_INCONSISTENT_STATE2, INSTANCE_INCONSISTENT_STATE3, INSTANCE_INCONSISTENT_STATE4,
    INSTANCE_INCONSISTENT_STATE5
)

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
import capa.xqueue_interface as xqueue_interface


log = logging.getLogger(__name__)

ORG = 'edX'
COURSE = 'open_ended'      # name of directory with course data


class OpenEndedChildTest(unittest.TestCase):
    """
    Test the open ended child class
    """
    location = Location("edX", "sa_test", "2012_Fall", "selfassessment", "SampleQuestion")

    metadata = json.dumps({'attempts': '10'})
    prompt = etree.XML("<prompt>This is a question prompt</prompt>")
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        <option>Second option</option>
        </category>
         </rubric></rubric>'''
    max_score = 1

    static_data = {
        'max_attempts': 20,
        'prompt': prompt,
        'rubric': rubric,
        'max_score': max_score,
        'display_name': 'Name',
        'accept_file_upload': False,
        'close_date': None,
        's3_interface': "",
        'open_ended_grading_interface': {},
        'skip_basic_checks': False,
        'control': {
            'required_peer_grading': 1,
            'peer_grader_count': 1,
            'min_to_calibrate': 3,
            'max_to_calibrate': 6,
            'peer_grade_finished_submissions_when_none_pending': False,
        }
    }
    definition = Mock()
    descriptor = Mock()

    def setUp(self):
        super(OpenEndedChildTest, self).setUp()
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.openendedchild = OpenEndedChild(self.test_system, self.location,
                                             self.definition, self.descriptor, self.static_data, self.metadata)

    def test_latest_answer_empty(self):
        answer = self.openendedchild.latest_answer()
        self.assertEqual(answer, "")

    def test_latest_score_empty(self):
        answer = self.openendedchild.latest_score()
        self.assertEqual(answer, None)

    def test_latest_post_assessment_empty(self):
        answer = self.openendedchild.latest_post_assessment(self.test_system)
        self.assertEqual(answer, "")

    def test_new_history_entry(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        answer = self.openendedchild.latest_answer()
        self.assertEqual(answer, new_answer)

        new_answer = "Newer Answer"
        self.openendedchild.new_history_entry(new_answer)
        answer = self.openendedchild.latest_answer()
        self.assertEqual(new_answer, answer)

    def test_record_latest_score(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        new_score = 3
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.latest_score()
        self.assertEqual(score, 3)

        new_score = 4
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.latest_score()
        self.assertEqual(score, 4)

    def test_record_latest_post_assessment(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)

        post_assessment = "Post assessment"
        self.openendedchild.record_latest_post_assessment(post_assessment)
        self.assertEqual(post_assessment,
                         self.openendedchild.latest_post_assessment(self.test_system))

    def test_get_score(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)

        score = self.openendedchild.get_score()
        self.assertEqual(score['score'], 0)
        self.assertEqual(score['total'], self.static_data['max_score'])

        new_score = 4
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.get_score()
        self.assertEqual(score['score'], new_score)
        self.assertEqual(score['total'], self.static_data['max_score'])

    def test_reset(self):
        self.openendedchild.reset(self.test_system)
        state = json.loads(self.openendedchild.get_instance_state())
        self.assertEqual(state['child_state'], OpenEndedChild.INITIAL)

    def test_is_last_response_correct(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(self.static_data['max_score'])
        self.assertEqual(self.openendedchild.is_last_response_correct(),
                         'correct')

        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(0)
        self.assertEqual(self.openendedchild.is_last_response_correct(),
                         'incorrect')


class OpenEndedModuleTest(unittest.TestCase):
    """
    Test the open ended module class
    """
    location = Location("edX", "sa_test", "2012_Fall", "selfassessment", "SampleQuestion")

    metadata = json.dumps({'attempts': '10'})
    prompt = etree.XML("<prompt>This is a question prompt</prompt>")
    rubric = etree.XML('''<rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric>''')
    max_score = 4

    static_data = {
        'max_attempts': 20,
        'prompt': prompt,
        'rubric': rubric,
        'max_score': max_score,
        'display_name': 'Name',
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

    oeparam = etree.XML('''
      <openendedparam>
            <initial_display>Enter essay here.</initial_display>
            <answer_display>This is the answer.</answer_display>
            <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
        </openendedparam>
    ''')
    definition = {'oeparam': oeparam}
    descriptor = Mock()

    feedback = {
        "success": True,
        "feedback": "Grader Feedback"
    }

    single_score_msg = {
        'correct': True,
        'score': 4,
        'msg': 'Grader Message',
        'feedback': json.dumps(feedback),
        'grader_type': 'IN',
        'grader_id': '1',
        'submission_id': '1',
        'success': True,
        'rubric_scores': [0],
        'rubric_scores_complete': True,
        'rubric_xml': etree.tostring(rubric)
    }

    multiple_score_msg = {
        'correct': True,
        'score': [0, 1],
        'msg': 'Grader Message',
        'feedback': [json.dumps(feedback), json.dumps(feedback)],
        'grader_type': 'PE',
        'grader_id': ['1', '2'],
        'submission_id': '1',
        'success': True,
        'rubric_scores': [[0], [0]],
        'rubric_scores_complete': [True, True],
        'rubric_xml': [etree.tostring(rubric), etree.tostring(rubric)]
    }

    def setUp(self):
        super(OpenEndedModuleTest, self).setUp()
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.test_system.location = self.location
        self.mock_xqueue = MagicMock()
        self.mock_xqueue.send_to_queue.return_value = (0, "Queued")

        def constructed_callback(dispatch="score_update"):
            return dispatch

        self.test_system.xqueue = {'interface': self.mock_xqueue, 'construct_callback': constructed_callback,
                                   'default_queuename': 'testqueue',
                                   'waittime': 1}
        self.openendedmodule = OpenEndedModule(self.test_system, self.location,
                                               self.definition, self.descriptor, self.static_data, self.metadata)

    def test_message_post(self):
        """Test message_post() sends feedback to xqueue."""

        submission_time = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)

        feedback_post = {
            'feedback': 'feedback text',
            'submission_id': '1',
            'grader_id': '1',
            'score': 3
        }
        result = self.openendedmodule.message_post(feedback_post, self.test_system)
        self.assertTrue(result['success'])

        # make sure it's actually sending something we want to the queue
        mock_send_to_queue_body_arg = json.loads(self.mock_xqueue.send_to_queue.call_args[1]['body'])
        self.assertEqual(mock_send_to_queue_body_arg['feedback'], feedback_post['feedback'])
        self.assertEqual(mock_send_to_queue_body_arg['submission_id'], int(feedback_post['submission_id']))
        self.assertEqual(mock_send_to_queue_body_arg['grader_id'], int(feedback_post['grader_id']))
        self.assertEqual(mock_send_to_queue_body_arg['score'], feedback_post['score'])
        body_arg_student_info = json.loads(mock_send_to_queue_body_arg['student_info'])
        self.assertEqual(body_arg_student_info['anonymous_student_id'], self.test_system.anonymous_student_id)
        self.assertGreaterEqual(body_arg_student_info['submission_time'], submission_time)

        state = json.loads(self.openendedmodule.get_instance_state())
        self.assertEqual(state['child_state'], OpenEndedModule.DONE)

    def test_message_post_fail(self):
        """Test message_post() if unable to send feedback to xqueue."""

        self.mock_xqueue.send_to_queue.return_value = (1, "Not Queued")

        feedback_post = {
            'feedback': 'feedback text',
            'submission_id': '1',
            'grader_id': '1',
            'score': 3
        }
        result = self.openendedmodule.message_post(feedback_post, self.test_system)
        self.assertFalse(result['success'])

        state = json.loads(self.openendedmodule.get_instance_state())
        self.assertNotEqual(state['child_state'], OpenEndedModule.DONE)

    def test_send_to_grader(self):
        student_response = "This is a student submission"
        submission_time = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)

        result, __ = self.openendedmodule.send_to_grader(student_response, self.test_system)
        self.assertTrue(result)

        mock_send_to_queue_body_arg = json.loads(self.mock_xqueue.send_to_queue.call_args[1]['body'])
        self.assertEqual(mock_send_to_queue_body_arg['student_response'], student_response)
        self.assertEqual(mock_send_to_queue_body_arg['max_score'], self.max_score)
        body_arg_student_info = json.loads(mock_send_to_queue_body_arg['student_info'])
        self.assertEqual(body_arg_student_info['anonymous_student_id'], self.test_system.anonymous_student_id)
        self.assertGreaterEqual(body_arg_student_info['submission_time'], submission_time)

    def test_send_to_grader_fail(self):
        """Test send_to_grader() if unable to send submission to xqueue."""

        student_response = "This is a student submission"
        self.mock_xqueue.send_to_queue.return_value = (1, "Not Queued")
        result, __ = self.openendedmodule.send_to_grader(student_response, self.test_system)
        self.assertFalse(result)

    def test_save_answer_fail(self):
        """Test save_answer() if unable to send submission to grader."""

        submission = "This is a student submission"
        self.openendedmodule.send_to_grader = Mock(return_value=(False, "Failed"))
        response = self.openendedmodule.save_answer(
            {"student_answer": submission},
            get_test_system()
        )
        self.assertFalse(response['success'])
        self.assertNotEqual(self.openendedmodule.latest_answer(), submission)
        self.assertEqual(self.openendedmodule.stored_answer, submission)
        state = json.loads(self.openendedmodule.get_instance_state())
        self.assertEqual(state['child_state'], OpenEndedModule.INITIAL)
        self.assertEqual(state['stored_answer'], submission)

    def update_score_single(self):
        self.openendedmodule.new_history_entry("New Entry")
        get = {'queuekey': "abcd",
               'xqueue_body': json.dumps(self.single_score_msg)}
        self.openendedmodule.update_score(get, self.test_system)

    def update_score_multiple(self):
        self.openendedmodule.new_history_entry("New Entry")
        get = {'queuekey': "abcd",
               'xqueue_body': json.dumps(self.multiple_score_msg)}
        self.openendedmodule.update_score(get, self.test_system)

    def test_latest_post_assessment(self):
        self.update_score_single()
        assessment = self.openendedmodule.latest_post_assessment(self.test_system)
        self.assertFalse(assessment == '')
        # check for errors
        self.assertFalse('errors' in assessment)

    def test_update_score_single(self):
        self.update_score_single()
        score = self.openendedmodule.latest_score()
        self.assertEqual(score, 4)

    def test_update_score_multiple(self):
        """
        Tests that a score of [0, 1] gets aggregated to 1.  A change in behavior added by @jbau
        """
        self.update_score_multiple()
        score = self.openendedmodule.latest_score()
        self.assertEquals(score, 1)

    @patch('xmodule.open_ended_grading_classes.open_ended_module.log.error')
    def test_update_score_nohistory(self, error_logger):
        """
        Tests error handling when there is no child_history
        """
        # NOTE that we are not creating any history items
        get = {'queuekey': "abcd",
               'xqueue_body': json.dumps(self.multiple_score_msg)}
        error_msg = ("Trying to update score without existing studentmodule child_history:\n"
                     "   location: i4x://edX/sa_test/selfassessment/SampleQuestion\n"
                     "   score: 1\n"
                     "   grader_ids: [u'1', u'2']\n"
                     "   submission_ids: [u'1', u'1']")
        self.openendedmodule.update_score(get, self.test_system)
        (msg,), _ = error_logger.call_args
        self.assertTrue(error_logger.called)
        self.assertEqual(msg, error_msg)

    def test_open_ended_display(self):
        """
        Test storing answer with the open ended module.
        """

        # Create a module with no state yet.  Important that this start off as a blank slate.
        test_module = OpenEndedModule(self.test_system, self.location,
                                      self.definition, self.descriptor, self.static_data, self.metadata)

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

        # Mock out the send_to_grader function so it doesn't try to connect to the xqueue.
        test_module.send_to_grader = Mock(return_value=(True, "Success"))
        # Submit a student response to the question.
        test_module.handle_ajax(
            "save_answer",
            {"student_answer": submitted_response},
            get_test_system()
        )
        # Submitting an answer should clear the stored answer.
        self.assertEqual(test_module.stored_answer, None)
        # Confirm that the answer is stored properly.
        self.assertEqual(test_module.latest_answer(), submitted_response)

    def test_parse_score_msg(self):
        """
        Test _parse_score_msg with empty dict.
        """

        assessment = self.openendedmodule._parse_score_msg("{}", self.test_system)
        self.assertEqual(assessment.get("valid"), False)


class CombinedOpenEndedModuleTest(unittest.TestCase):
    """
    Unit tests for the combined open ended xmodule
    """
    location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion")
    definition_template = """
                    <combinedopenended attempts="10000">
                    {rubric}
                    {prompt}
                    <task>
                    {task1}
                    </task>
                    <task>
                    {task2}
                    </task>
                    </combinedopenended>
                    """
    prompt = "<prompt>This is a question prompt</prompt>"
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        <option>Second option</option>
        </category>
         </rubric></rubric>'''
    max_score = 1

    metadata = {'attempts': '10', 'max_score': max_score}

    static_data = {
        'max_attempts': 20,
        'prompt': prompt,
        'rubric': rubric,
        'max_score': max_score,
        'display_name': 'Name',
        'accept_file_upload': False,
        'close_date': "",
        's3_interface': test_util_open_ended.S3_INTERFACE,
        'open_ended_grading_interface': test_util_open_ended.OPEN_ENDED_GRADING_INTERFACE,
        'skip_basic_checks': False,
        'graded': True,
    }

    oeparam = etree.XML('''
      <openendedparam>
            <initial_display>Enter essay here.</initial_display>
            <answer_display>This is the answer.</answer_display>
            <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
        </openendedparam>
    ''')

    task_xml1 = '''
                <selfassessment>
                    <hintprompt>
                        What hint about this problem would you give to someone?
                    </hintprompt>
                    <submitmessage>
                        Save Succcesful.  Thanks for participating!
                    </submitmessage>
                </selfassessment>
            '''
    task_xml2 = '''
    <openended min_score_to_attempt="1" max_score_to_attempt="1">
            <openendedparam>
                    <initial_display>Enter essay here.</initial_display>
                    <answer_display>This is the answer.</answer_display>
                    <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
           </openendedparam>
    </openended>'''
    definition = {'prompt': etree.XML(prompt), 'rubric': etree.XML(rubric), 'task_xml': [task_xml1, task_xml2]}
    full_definition = definition_template.format(prompt=prompt, rubric=rubric, task1=task_xml1, task2=task_xml2)
    descriptor = Mock(data=full_definition)
    test_system = get_test_system()
    test_system.open_ended_grading_interface = None
    usage_key = test_system.course_id.make_usage_key('combinedopenended', 'test_loc')
    # ScopeIds has 4 fields: user_id, block_type, def_id, usage_id
    scope_ids = ScopeIds(1, 'combinedopenended', usage_key, usage_key)
    combinedoe_container = CombinedOpenEndedModule(
        descriptor=descriptor,
        runtime=test_system,
        field_data=DictFieldData({
            'data': full_definition,
            'weight': '1',
        }),
        scope_ids=scope_ids,
    )

    def setUp(self):
        super(CombinedOpenEndedModuleTest, self).setUp()
        self.combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                                    self.location,
                                                    self.definition,
                                                    self.descriptor,
                                                    static_data=self.static_data,
                                                    metadata=self.metadata,
                                                    instance_state=self.static_data)

    def test_get_tag_name(self):
        """
        Test to see if the xml tag name is correct
        """
        name = self.combinedoe.get_tag_name("<t>Tag</t>")
        self.assertEqual(name, "t")

    def test_get_last_response(self):
        """
        See if we can parse the last response
        """
        response_dict = self.combinedoe.get_last_response(0)
        self.assertEqual(response_dict['type'], "selfassessment")
        self.assertEqual(response_dict['max_score'], self.max_score)
        self.assertEqual(response_dict['state'], CombinedOpenEndedV1Module.INITIAL)

    def test_create_task(self):
        combinedoe = self.generate_oe_module(TEST_STATE_AI, 1, [self.task_xml1, self.task_xml2])

        first_task = combinedoe.create_task(combinedoe.task_states[0], combinedoe.task_xml[0])
        self.assertIsInstance(first_task, SelfAssessmentModule)

        second_task = combinedoe.create_task(combinedoe.task_states[1], combinedoe.task_xml[1])
        self.assertIsInstance(second_task, OpenEndedModule)

    def test_get_task_number(self):
        combinedoe = self.generate_oe_module(TEST_STATE_AI, 1, [self.task_xml1, self.task_xml2])

        first_task = combinedoe.get_task_number(0)
        self.assertIsInstance(first_task, SelfAssessmentModule)

        second_task = combinedoe.get_task_number(1)
        self.assertIsInstance(second_task, OpenEndedModule)

        third_task = combinedoe.get_task_number(2)
        self.assertIsNone(third_task)

    def test_update_task_states(self):
        """
        See if we can update the task states properly
        """
        changed = self.combinedoe.update_task_states()
        self.assertFalse(changed)

        current_task = self.combinedoe.current_task
        current_task.change_state(CombinedOpenEndedV1Module.DONE)
        changed = self.combinedoe.update_task_states()

        self.assertTrue(changed)

    def test_get_max_score(self):
        """
        Try to get the max score of the problem
        """
        self.combinedoe.update_task_states()
        self.combinedoe.state = "done"
        self.combinedoe.is_scored = True
        max_score = self.combinedoe.max_score()
        self.assertEqual(max_score, 1)

    def test_container_get_max_score(self):
        """
        See if we can get the max score from the actual xmodule
        """
        # The progress view requires that this function be exposed
        max_score = self.combinedoe_container.max_score()
        self.assertEqual(max_score, None)

    def test_container_get_progress(self):
        """
        See if we can get the progress from the actual xmodule
        """
        progress = self.combinedoe_container.max_score()
        self.assertEqual(progress, None)

    def test_get_progress(self):
        """
        Test if we can get the correct progress from the combined open ended class
        """
        self.combinedoe.update_task_states()
        self.combinedoe.state = "done"
        self.combinedoe.is_scored = True
        progress = self.combinedoe.get_progress()
        self.assertIsInstance(progress, Progress)

        # progress._a is the score of the xmodule, which is 0 right now.
        self.assertEqual(progress._a, 0)

        # progress._b is the max_score (which is 1), divided by the weight (which is 1).
        self.assertEqual(progress._b, 1)

    def test_container_weight(self):
        """
        Check the problem weight in the container
        """
        weight = self.combinedoe_container.weight
        self.assertEqual(weight, 1)

    def test_container_child_weight(self):
        """
        Test the class to see if it picks up the right weight
        """
        weight = self.combinedoe_container.child_module.weight
        self.assertEqual(weight, 1)

    def test_get_score(self):
        """
        See if scoring works
        """
        score_dict = self.combinedoe.get_score()
        self.assertEqual(score_dict['score'], 0)
        self.assertEqual(score_dict['total'], 1)

    def test_alternate_orderings(self):
        """
        Try multiple ordering of definitions to see if the problem renders different steps correctly.
        """
        t1 = self.task_xml1
        t2 = self.task_xml2
        xml_to_test = [[t1], [t2], [t1, t1], [t1, t2], [t2, t2], [t2, t1], [t1, t2, t1]]
        for xml in xml_to_test:
            definition = {'prompt': etree.XML(self.prompt), 'rubric': etree.XML(self.rubric), 'task_xml': xml}
            descriptor = Mock(data=definition)
            combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                                   self.location,
                                                   definition,
                                                   descriptor,
                                                   static_data=self.static_data,
                                                   metadata=self.metadata,
                                                   instance_state=self.static_data)

            changed = combinedoe.update_task_states()
            self.assertFalse(changed)

            combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                                   self.location,
                                                   definition,
                                                   descriptor,
                                                   static_data=self.static_data,
                                                   metadata=self.metadata,
                                                   instance_state={'task_states': TEST_STATE_SA})

            combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                                   self.location,
                                                   definition,
                                                   descriptor,
                                                   static_data=self.static_data,
                                                   metadata=self.metadata,
                                                   instance_state={'task_states': TEST_STATE_SA_IN})

    def test_get_score_realistic(self):
        """
        Try to parse the correct score from a json instance state
        """
        instance_state = json.loads(MOCK_INSTANCE_STATE)
        rubric = """
        <rubric>
            <rubric>
                <category>
                    <description>Response Quality</description>
                    <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
                    <option>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option>
                    <option>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option>
                    <option>The response is correct, complete, and contains evidence of higher-order thinking.</option>
                </category>
            </rubric>
        </rubric>
        """
        definition = {'prompt': etree.XML(self.prompt), 'rubric': etree.XML(rubric),
                      'task_xml': [self.task_xml1, self.task_xml2]}
        descriptor = Mock(data=definition)
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               definition,
                                               descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=instance_state)
        score_dict = combinedoe.get_score()
        self.assertEqual(score_dict['score'], 15.0)
        self.assertEqual(score_dict['total'], 15.0)

    def generate_oe_module(self, task_state, task_number, task_xml):
        """
        Return a combined open ended module with the specified parameters
        """
        definition = {
            'prompt': etree.XML(self.prompt),
            'rubric': etree.XML(self.rubric),
            'task_xml': task_xml
        }
        descriptor = Mock(data=definition)
        module = Mock(scope_ids=Mock(usage_id='dummy-usage-id'))
        instance_state = {'task_states': task_state, 'graded': True}
        if task_number is not None:
            instance_state.update({'current_task_number': task_number})
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               definition,
                                               descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=instance_state)
        return combinedoe

    def ai_state_reset(self, task_state, task_number=None):
        """
        See if state is properly reset
        """
        combinedoe = self.generate_oe_module(task_state, task_number, [self.task_xml2])
        html = combinedoe.get_html()
        self.assertIsInstance(html, basestring)

        score = combinedoe.get_score()
        if combinedoe.is_scored:
            self.assertEqual(score['score'], 0)
        else:
            self.assertEqual(score['score'], None)

    def ai_state_success(self, task_state, task_number=None, iscore=2, tasks=None):
        """
        See if state stays the same
        """
        if tasks is None:
            tasks = [self.task_xml1, self.task_xml2]
        combinedoe = self.generate_oe_module(task_state, task_number, tasks)
        html = combinedoe.get_html()
        self.assertIsInstance(html, basestring)
        score = combinedoe.get_score()
        self.assertEqual(int(score['score']), iscore)

    def test_ai_state_reset(self):
        self.ai_state_reset(TEST_STATE_AI)

    def test_ai_state2_reset(self):
        self.ai_state_reset(TEST_STATE_AI2)

    def test_ai_invalid_state(self):
        self.ai_state_reset(TEST_STATE_AI2_INVALID)

    def test_ai_state_rest_task_number(self):
        self.ai_state_reset(TEST_STATE_AI, task_number=2)
        self.ai_state_reset(TEST_STATE_AI, task_number=5)
        self.ai_state_reset(TEST_STATE_AI, task_number=1)
        self.ai_state_reset(TEST_STATE_AI, task_number=0)

    def test_ai_state_success(self):
        self.ai_state_success(TEST_STATE_AI)

    def test_state_single(self):
        self.ai_state_success(TEST_STATE_SINGLE, iscore=12)

    def test_state_pe_single(self):
        self.ai_state_success(TEST_STATE_PE_SINGLE, iscore=0, tasks=[self.task_xml2])

    def test_deprecation_message(self):
        """
        Test the validation message produced for deprecation.
        """
        # pylint: disable=no-member
        validation = self.combinedoe_container.validate()
        deprecation_msg = "ORA1 is no longer supported. To use this assessment, " \
                          "replace this ORA1 component with an ORA2 component."
        validation.summary.text = deprecation_msg
        validation.summary.type = 'error'

        self.assertEqual(
            validation.summary.text,
            deprecation_msg
        )
        self.assertEqual(validation.summary.type, StudioValidationMessage.ERROR)


class CombinedOpenEndedModuleConsistencyTest(unittest.TestCase):
    """
    Unit tests for the combined open ended xmodule rubric scores consistency.
    """

    # location, definition_template, prompt, rubric, max_score, metadata, oeparam, task_xml1, task_xml2
    # All these variables are used to construct the xmodule descriptor.
    location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion")
    definition_template = """
                    <combinedopenended attempts="10000">
                    {rubric}
                    {prompt}
                    <task>
                    {task1}
                    </task>
                    <task>
                    {task2}
                    </task>
                    </combinedopenended>
                    """
    prompt = "<prompt>This is a question prompt</prompt>"
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        <option>Second option</option>
        </category>
         </rubric></rubric>'''
    max_score = 10

    metadata = {'attempts': '10', 'max_score': max_score}

    oeparam = etree.XML('''
      <openendedparam>
            <initial_display>Enter essay here.</initial_display>
            <answer_display>This is the answer.</answer_display>
            <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
        </openendedparam>
    ''')

    task_xml1 = '''
                <selfassessment>
                    <hintprompt>
                        What hint about this problem would you give to someone?
                    </hintprompt>
                    <submitmessage>
                        Save Succcesful.  Thanks for participating!
                    </submitmessage>
                </selfassessment>
            '''
    task_xml2 = '''
    <openended min_score_to_attempt="1" max_score_to_attempt="10">
            <openendedparam>
                    <initial_display>Enter essay here.</initial_display>
                    <answer_display>This is the answer.</answer_display>
                    <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
           </openendedparam>
    </openended>'''

    static_data = {
        'max_attempts': 20,
        'prompt': prompt,
        'rubric': rubric,
        'max_score': max_score,
        'display_name': 'Name',
        'accept_file_upload': False,
        'close_date': "",
        's3_interface': test_util_open_ended.S3_INTERFACE,
        'open_ended_grading_interface': test_util_open_ended.OPEN_ENDED_GRADING_INTERFACE,
        'skip_basic_checks': False,
        'graded': True,
    }

    definition = {'prompt': etree.XML(prompt), 'rubric': etree.XML(rubric), 'task_xml': [task_xml1, task_xml2]}
    full_definition = definition_template.format(prompt=prompt, rubric=rubric, task1=task_xml1, task2=task_xml2)
    descriptor = Mock(data=full_definition)
    test_system = get_test_system()
    test_system.open_ended_grading_interface = None
    usage_key = test_system.course_id.make_usage_key('combinedopenended', 'test_loc')
    # ScopeIds has 4 fields: user_id, block_type, def_id, usage_id
    scope_ids = ScopeIds(1, 'combinedopenended', usage_key, usage_key)
    combinedoe_container = CombinedOpenEndedModule(
        descriptor=descriptor,
        runtime=test_system,
        field_data=DictFieldData({
            'data': full_definition,
            'weight': '1',
        }),
        scope_ids=scope_ids,
    )

    def setUp(self):
        super(CombinedOpenEndedModuleConsistencyTest, self).setUp()
        self.combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                                    self.location,
                                                    self.definition,
                                                    self.descriptor,
                                                    static_data=self.static_data,
                                                    metadata=self.metadata,
                                                    instance_state=json.loads(INSTANCE_INCONSISTENT_STATE))

    def test_get_score(self):
        """
        If grader type is ML score should be updated from rubric scores. Aggregate rubric scores = sum([3])*5.
        """
        score_dict = self.combinedoe.get_score()
        self.assertEqual(score_dict['score'], 15.0)
        self.assertEqual(score_dict['total'], 5.0)

    def test_get_score_with_pe_grader(self):
        """
        If grader type is PE score should not be updated from rubric scores. Aggregate rubric scores = sum([3])*5.
        """
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               self.definition,
                                               self.descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=json.loads(INSTANCE_INCONSISTENT_STATE2))
        score_dict = combinedoe.get_score()
        self.assertNotEqual(score_dict['score'], 15.0)

    def test_get_score_with_different_score_value_in_rubric(self):
        """
        If grader type is ML score should be updated from rubric scores. Aggregate rubric scores = sum([5])*5.
        """
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               self.definition,
                                               self.descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=json.loads(INSTANCE_INCONSISTENT_STATE3))
        score_dict = combinedoe.get_score()
        self.assertEqual(score_dict['score'], 25.0)
        self.assertEqual(score_dict['total'], 5.0)

    def test_get_score_with_old_task_states(self):
        """
        If grader type is ML and old_task_states are present in instance inconsistent state score should be updated
        from rubric scores. Aggregate rubric scores = sum([3])*5.
        """
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               self.definition,
                                               self.descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=json.loads(INSTANCE_INCONSISTENT_STATE4))
        score_dict = combinedoe.get_score()
        self.assertEqual(score_dict['score'], 15.0)
        self.assertEqual(score_dict['total'], 5.0)

    def test_get_score_with_score_missing(self):
        """
        If grader type is ML and score field is missing in instance inconsistent state score should be updated from
        rubric scores. Aggregate rubric scores = sum([3])*5.
        """
        combinedoe = CombinedOpenEndedV1Module(self.test_system,
                                               self.location,
                                               self.definition,
                                               self.descriptor,
                                               static_data=self.static_data,
                                               metadata=self.metadata,
                                               instance_state=json.loads(INSTANCE_INCONSISTENT_STATE5))
        score_dict = combinedoe.get_score()
        self.assertEqual(score_dict['score'], 15.0)
        self.assertEqual(score_dict['total'], 5.0)


class OpenEndedModuleXmlTest(unittest.TestCase, DummyModulestore):
    """
    Test the student flow in the combined open ended xmodule
    """
    problem_location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion")
    answer = "blah blah"
    assessment = [0, 1]
    hint = "blah"

    def get_module_system(self, descriptor):

        def construct_callback(dispatch="score_update"):
            return dispatch

        test_system = get_test_system()
        test_system.open_ended_grading_interface = None
        test_system.xqueue['interface'] = Mock(
            send_to_queue=Mock(return_value=(0, "Queued"))
        )
        test_system.xqueue['construct_callback'] = construct_callback

        return test_system

    def setUp(self):
        super(OpenEndedModuleXmlTest, self).setUp()
        self.setup_modulestore(COURSE)

    def _handle_ajax(self, dispatch, content):
        # Load the module from persistence
        module = self._module()

        # Call handle_ajax on the module
        result = module.handle_ajax(dispatch, content)

        # Persist the state
        module.save()

        return result

    def _module(self):
        return self.get_module_from_location(self.problem_location)

    def test_open_ended_load_and_save(self):
        """
        See if we can load the module and save an answer
        @return:
        """
        # Try saving an answer
        self._handle_ajax("save_answer", {"student_answer": self.answer})

        task_one_json = json.loads(self._module().task_states[0])
        self.assertEqual(task_one_json['child_history'][0]['answer'], self.answer)

    def test_open_ended_flow_reset(self):
        """
        Test the flow of the module if we complete the self assessment step and then reset
        @return:
        """
        assessment = [0, 1]

        # Simulate a student saving an answer
        self._handle_ajax("get_html", {})
        self._handle_ajax("save_answer", {"student_answer": self.answer})
        self._handle_ajax("get_html", {})

        # Mock a student submitting an assessment
        assessment_dict = MultiDict({'assessment': sum(assessment)})
        assessment_dict.extend(('score_list[]', val) for val in assessment)

        self._handle_ajax("save_assessment", assessment_dict)

        task_one_json = json.loads(self._module().task_states[0])
        self.assertEqual(json.loads(task_one_json['child_history'][0]['post_assessment']), assessment)

        self._handle_ajax("get_combined_rubric", {})

        # Move to the next step in the problem
        self._handle_ajax("next_problem", {})
        self.assertEqual(self._module().current_task_number, 0)

        html = self._module().render(STUDENT_VIEW).content
        self.assertIsInstance(html, basestring)

        rubric = self._handle_ajax("get_combined_rubric", {})
        self.assertIsInstance(rubric, basestring)

        self.assertEqual(self._module().state, "assessing")

        self._handle_ajax("reset", {})
        self.assertEqual(self._module().current_task_number, 0)

    def test_open_ended_flow_with_xqueue_failure(self):
        """
        Test a two step problem where the student first goes through the self assessment step, and then the
        open ended step with the xqueue failing in the first step.
        """
        assessment = [1, 1]

        # Simulate a student saving an answer
        self._handle_ajax("save_answer", {"student_answer": self.answer})
        status = self._handle_ajax("get_status", {})
        self.assertIsInstance(status, basestring)

        # Mock a student submitting an assessment
        assessment_dict = MultiDict({'assessment': sum(assessment)})
        assessment_dict.extend(('score_list[]', val) for val in assessment)

        mock_xqueue_interface = Mock(
            send_to_queue=Mock(return_value=(1, "Not Queued"))
        )

        # Call handle_ajax on the module with xqueue down
        module = self._module()
        with patch.dict(module.xmodule_runtime.xqueue, {'interface': mock_xqueue_interface}):
            module.handle_ajax("save_assessment", assessment_dict)
            self.assertEqual(module.current_task_number, 1)
            self.assertTrue((module.child_module.get_task_number(1).child_created))
        module.save()

        # Check that next time the OpenEndedModule is loaded it calls send_to_grader
        with patch.object(OpenEndedModule, 'send_to_grader') as mock_send_to_grader:
            mock_send_to_grader.return_value = (False, "Not Queued")
            module = self._module().child_module.get_score()
            self.assertTrue(mock_send_to_grader.called)
            self.assertTrue((self._module().child_module.get_task_number(1).child_created))

        # Loading it this time should send submission to xqueue correctly
        self.assertFalse((self._module().child_module.get_task_number(1).child_created))
        self.assertEqual(self._module().current_task_number, 1)
        self.assertEqual(self._module().state, OpenEndedChild.ASSESSING)

        task_one_json = json.loads(self._module().task_states[0])
        self.assertEqual(json.loads(task_one_json['child_history'][0]['post_assessment']), assessment)

        # Move to the next step in the problem
        self._handle_ajax("next_problem", {})
        self.assertEqual(self._module().current_task_number, 1)
        self._module().render(STUDENT_VIEW)

        # Try to get the rubric from the module
        self._handle_ajax("get_combined_rubric", {})

        self.assertEqual(self._module().state, OpenEndedChild.ASSESSING)

        # Make a fake reply from the queue
        queue_reply = {
            'queuekey': "",
            'xqueue_body': json.dumps({
                'score': 0,
                'feedback': json.dumps({"spelling": "Spelling: Ok.", "grammar": "Grammar: Ok.",
                                        "markup-text": " all of us can think of a book that we hope none of our children or any other children have taken off the shelf . but if i have the right to remove that book from the shelf that work i abhor then you also have exactly the same right and so does everyone else . and then we <bg>have no books left</bg> on the shelf for any of us . <bs>katherine</bs> <bs>paterson</bs> , author write a persuasive essay to a newspaper reflecting your vies on censorship <bg>in libraries . do</bg> you believe that certain materials , such as books , music , movies , magazines , <bg>etc . , should be</bg> removed from the shelves if they are found <bg>offensive ? support your</bg> position with convincing arguments from your own experience , observations <bg>, and or reading .</bg> "}),
                'grader_type': "ML",
                'success': True,
                'grader_id': 1,
                'submission_id': 1,
                'rubric_xml': "<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>",
                'rubric_scores_complete': True,
            })
        }

        self._handle_ajax("check_for_score", {})

        # Update the module with the fake queue reply
        self._handle_ajax("score_update", queue_reply)

        module = self._module()
        self.assertFalse(module.ready_to_reset)
        self.assertEqual(module.current_task_number, 1)

        # Get html and other data client will request
        module.render(STUDENT_VIEW)

        self._handle_ajax("skip_post_assessment", {})

        # Get all results
        self._handle_ajax("get_combined_rubric", {})

        # reset the problem
        self._handle_ajax("reset", {})
        self.assertEqual(self._module().state, "initial")

    def test_open_ended_flow_correct(self):
        """
        Test a two step problem where the student first goes through the self assessment step, and then the
        open ended step.
        @return:
        """
        assessment = [1, 1]

        # Simulate a student saving an answer
        self._handle_ajax("save_answer", {"student_answer": self.answer})
        status = self._handle_ajax("get_status", {})
        self.assertIsInstance(status, basestring)

        # Mock a student submitting an assessment
        assessment_dict = MultiDict({'assessment': sum(assessment)})
        assessment_dict.extend(('score_list[]', val) for val in assessment)

        self._handle_ajax("save_assessment", assessment_dict)

        task_one_json = json.loads(self._module().task_states[0])
        self.assertEqual(json.loads(task_one_json['child_history'][0]['post_assessment']), assessment)

        # Move to the next step in the problem
        self._handle_ajax("next_problem", {})
        self.assertEqual(self._module().current_task_number, 1)
        self._module().render(STUDENT_VIEW)

        # Try to get the rubric from the module
        self._handle_ajax("get_combined_rubric", {})

        # Make a fake reply from the queue
        queue_reply = {
            'queuekey': "",
            'xqueue_body': json.dumps({
                'score': 0,
                'feedback': json.dumps({"spelling": "Spelling: Ok.", "grammar": "Grammar: Ok.",
                                        "markup-text": " all of us can think of a book that we hope none of our children or any other children have taken off the shelf . but if i have the right to remove that book from the shelf that work i abhor then you also have exactly the same right and so does everyone else . and then we <bg>have no books left</bg> on the shelf for any of us . <bs>katherine</bs> <bs>paterson</bs> , author write a persuasive essay to a newspaper reflecting your vies on censorship <bg>in libraries . do</bg> you believe that certain materials , such as books , music , movies , magazines , <bg>etc . , should be</bg> removed from the shelves if they are found <bg>offensive ? support your</bg> position with convincing arguments from your own experience , observations <bg>, and or reading .</bg> "}),
                'grader_type': "ML",
                'success': True,
                'grader_id': 1,
                'submission_id': 1,
                'rubric_xml': "<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>",
                'rubric_scores_complete': True,
            })
        }

        self._handle_ajax("check_for_score", {})

        # Update the module with the fake queue reply
        self._handle_ajax("score_update", queue_reply)

        module = self._module()
        self.assertFalse(module.ready_to_reset)
        self.assertEqual(module.current_task_number, 1)

        # Get html and other data client will request
        module.render(STUDENT_VIEW)

        self._handle_ajax("skip_post_assessment", {})

        # Get all results
        self._handle_ajax("get_combined_rubric", {})

        # reset the problem
        self._handle_ajax("reset", {})
        self.assertEqual(self._module().state, "initial")


class OpenEndedModuleXmlAttemptTest(unittest.TestCase, DummyModulestore):
    """
    Test if student is able to reset the problem
    """
    problem_location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion1Attempt")
    answer = "blah blah"
    assessment = [0, 1]
    hint = "blah"

    def get_module_system(self, descriptor):
        test_system = get_test_system()
        test_system.open_ended_grading_interface = None
        test_system.xqueue['interface'] = Mock(
            send_to_queue=Mock(return_value=(0, "Queued"))
        )
        return test_system

    def setUp(self):
        super(OpenEndedModuleXmlAttemptTest, self).setUp()
        self.setup_modulestore(COURSE)

    def _handle_ajax(self, dispatch, content):
        # Load the module from persistence
        module = self._module()

        # Call handle_ajax on the module
        result = module.handle_ajax(dispatch, content)

        # Persist the state
        module.save()

        return result

    def _module(self):
        return self.get_module_from_location(self.problem_location)

    def test_reset_fail(self):
        """
       Test the flow of the module if we complete the self assessment step and then reset
       Since the problem only allows one attempt, should fail.
       @return:
       """
        assessment = [0, 1]

        # Simulate a student saving an answer
        self._handle_ajax("save_answer", {"student_answer": self.answer})

        # Mock a student submitting an assessment
        assessment_dict = MultiDict({'assessment': sum(assessment)})
        assessment_dict.extend(('score_list[]', val) for val in assessment)

        self._handle_ajax("save_assessment", assessment_dict)
        task_one_json = json.loads(self._module().task_states[0])
        self.assertEqual(json.loads(task_one_json['child_history'][0]['post_assessment']), assessment)

        # Move to the next step in the problem
        self._handle_ajax("next_problem", {})
        self.assertEqual(self._module().current_task_number, 0)

        html = self._module().render(STUDENT_VIEW).content
        self.assertIsInstance(html, basestring)

        # Module should now be done
        rubric = self._handle_ajax("get_combined_rubric", {})
        self.assertIsInstance(rubric, basestring)
        self.assertEqual(self._module().state, "done")

        # Try to reset, should fail because only 1 attempt is allowed
        reset_data = json.loads(self._handle_ajax("reset", {}))
        self.assertEqual(reset_data['success'], False)


class OpenEndedModuleXmlImageUploadTest(unittest.TestCase, DummyModulestore):
    """
    Test if student is able to upload images properly.
    """
    problem_location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestionImageUpload")
    answer_text = "Hello, this is my amazing answer."
    file_text = "Hello, this is my amazing file."
    file_name = "Student file 1"
    answer_link = "http://www.edx.org"
    autolink_tag = '<a target="_blank" href='
    autolink_tag_swapped = '<a href='

    def get_module_system(self, descriptor):
        test_system = get_test_system()
        test_system.open_ended_grading_interface = None
        test_system.s3_interface = test_util_open_ended.S3_INTERFACE
        test_system.xqueue['interface'] = Mock(
            send_to_queue=Mock(return_value=(0, "Queued"))
        )
        return test_system

    def setUp(self):
        super(OpenEndedModuleXmlImageUploadTest, self).setUp()
        self.setup_modulestore(COURSE)

    def test_file_upload_fail(self):
        """
        Test to see if a student submission without a file attached fails.
        """
        module = self.get_module_from_location(self.problem_location)

        # Simulate a student saving an answer
        response = module.handle_ajax("save_answer", {"student_answer": self.answer_text})
        response = json.loads(response)
        self.assertFalse(response['success'])
        self.assertIn('error', response)

    @patch(
        'xmodule.open_ended_grading_classes.openendedchild.S3Connection',
        test_util_open_ended.MockS3Connection
    )
    @patch(
        'xmodule.open_ended_grading_classes.openendedchild.Key',
        test_util_open_ended.MockS3Key
    )
    def test_file_upload_success(self):
        """
        Test to see if a student submission with a file is handled properly.
        """
        module = self.get_module_from_location(self.problem_location)

        # Simulate a student saving an answer with a file
        response = module.handle_ajax("save_answer", {
            "student_answer": self.answer_text,
            "valid_files_attached": True,
            "student_file": [MockUploadedFile(self.file_name, self.file_text)],
        })

        response = json.loads(response)
        self.assertTrue(response['success'])
        self.assertIn(self.file_name, response['student_response'])
        self.assertTrue(self.autolink_tag in response['student_response'] or
                        self.autolink_tag_swapped in response['student_response'])

    def test_link_submission_success(self):
        """
        Students can submit links instead of files.  Check that the link is properly handled.
        """
        module = self.get_module_from_location(self.problem_location)

        # Simulate a student saving an answer with a link.
        response = module.handle_ajax("save_answer", {
            "student_answer": "{0} {1}".format(self.answer_text, self.answer_link)
        })

        response = json.loads(response)

        self.assertTrue(response['success'])
        self.assertIn(self.answer_link, response['student_response'])
        self.assertTrue(self.autolink_tag in response['student_response'] or
                        self.autolink_tag_swapped in response['student_response'])


class OpenEndedModuleUtilTest(unittest.TestCase):
    """
    Tests for the util functions of OpenEndedModule.  Currently just for the html_sanitizer and <br/> inserter
    """
    script_dirty = u'<script>alert("xss!")</script>'
    script_clean = u'alert("xss!")'
    img_dirty = u'<img alt="cats" height="200" onclick="eval()" src="http://example.com/lolcats.jpg" width="200">'
    img_clean = u'<img width="200" alt="cats" height="200" src="http://example.com/lolcats.jpg">'
    embed_dirty = u'<embed height="200" id="cats" onhover="eval()" src="http://example.com/lolcats.swf" width="200"/>'
    embed_clean = u'<embed width="200" height="200" id="cats" src="http://example.com/lolcats.swf">'
    iframe_dirty = u'<iframe class="cats" height="200" onerror="eval()" src="http://example.com/lolcats" width="200"/>'
    iframe_clean = ur'<iframe (height="200" ?|class="cats" ?|width="200" ?|src="http://example.com/lolcats" ?)+></iframe>'

    text = u'I am a \u201c\xfcber student\u201d'
    text_lessthan_noencd = u'This used to be broken < by the other parser. 3>5'
    text_lessthan_encode = u'This used to be broken &lt; by the other parser. 3&gt;5'
    text_linebreaks = u"St\xfcdent submission:\nI like lamp."
    text_brs = u"St\xfcdent submission:<br/>I like lamp."

    link_text = u'I love going to www.lolcatz.com'
    link_atag = u'I love going to <a target="_blank" href="http://www.lolcatz.com">www.lolcatz.com</a>'

    def assertHtmlEqual(self, actual, expected):
        """
        Assert that two strings represent the same html.
        """
        return self._assertHtmlEqual(
            fragment_fromstring(actual, create_parent='div'),
            fragment_fromstring(expected, create_parent='div')
        )

    def _assertHtmlEqual(self, actual, expected):
        """
        Assert that two HTML ElementTree elements are equal.
        """
        self.assertEqual(actual.tag, expected.tag)
        self.assertEqual(actual.attrib, expected.attrib)
        self.assertEqual(actual.text, expected.text)
        self.assertEqual(actual.tail, expected.tail)
        self.assertEqual(len(actual), len(expected))
        for actual_child, expected_child in zip(actual, expected):
            self._assertHtmlEqual(actual_child, expected_child)

    def test_script(self):
        """
        Basic test for stripping <script>
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.script_dirty), self.script_clean)

    def test_img(self):
        """
        Basic test for passing through img, but stripping bad attr
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.img_dirty), self.img_clean)

    def test_embed(self):
        """
        Basic test for passing through embed, but stripping bad attr
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.embed_dirty), self.embed_clean)

    def test_iframe(self):
        """
        Basic test for passing through iframe, but stripping bad attr
        """
        self.assertRegexpMatches(OpenEndedChild.sanitize_html(self.iframe_dirty), self.iframe_clean)

    def test_text(self):
        """
        Test for passing through text unchanged, including unicode
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.text), self.text)

    def test_lessthan(self):
        """
        Tests that `<` in text context is handled properly
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.text_lessthan_noencd), self.text_lessthan_encode)

    def test_linebreaks(self):
        """
        tests the replace_newlines function
        """
        self.assertHtmlEqual(OpenEndedChild.replace_newlines(self.text_linebreaks), self.text_brs)

    def test_linkify(self):
        """
        tests the replace_newlines function
        """
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(self.link_text), self.link_atag)

    def test_combined(self):
        """
        tests a combination of inputs
        """
        test_input = u"{}\n{}\n{}\n\n{}{}\n{}".format(self.link_text,
                                                      self.text,
                                                      self.script_dirty,
                                                      self.embed_dirty,
                                                      self.text_lessthan_noencd,
                                                      self.img_dirty)
        test_output = u"{}<br/>{}<br/>{}<br/><br/>{}{}<br/>{}".format(self.link_atag,
                                                                      self.text,
                                                                      self.script_clean,
                                                                      self.embed_clean,
                                                                      self.text_lessthan_encode,
                                                                      self.img_clean)
        self.assertHtmlEqual(OpenEndedChild.sanitize_html(test_input), test_output)
