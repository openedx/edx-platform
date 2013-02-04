import json
from mock import Mock, MagicMock, ANY
import unittest

from xmodule.openendedchild import OpenEndedChild
from xmodule.open_ended_module import OpenEndedModule
from xmodule.combined_open_ended_module import CombinedOpenEndedModule

from xmodule.modulestore import Location
from lxml import etree
import capa.xqueue_interface as xqueue_interface
from datetime import datetime

from . import test_system
"""
Tests for the various pieces of the CombinedOpenEndedGrading system

OpenEndedChild
OpenEndedModule

"""

class OpenEndedChildTest(unittest.TestCase):
    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

    metadata = json.dumps({'attempts': '10'})
    prompt = etree.XML("<prompt>This is a question prompt</prompt>")
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric></rubric>'''
    max_score = 4

    static_data = {
            'max_attempts': 20,
            'prompt': prompt,
            'rubric': rubric,
            'max_score': max_score, 
            'display_name': 'Name',
            'accept_file_upload' : False,
            }
    definition = Mock()
    descriptor = Mock()

    def setUp(self):
        self.openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 
 

    def test_latest_answer_empty(self):
        answer = self.openendedchild.latest_answer()
        self.assertEqual(answer, "")


    def test_latest_score_empty(self):
        answer = self.openendedchild.latest_score()
        self.assertEqual(answer, None)


    def test_latest_post_assessment_empty(self):
        answer = self.openendedchild.latest_post_assessment(test_system)
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
                self.openendedchild.latest_post_assessment(test_system))

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
        self.openendedchild.reset(test_system)
        state = json.loads(self.openendedchild.get_instance_state())
        self.assertEqual(state['state'], OpenEndedChild.INITIAL)
        

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
    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

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

    def setUp(self):
        test_system.location = self.location
        self.mock_xqueue = MagicMock()
        self.mock_xqueue.send_to_queue.return_value=(None, "Message")
        test_system.xqueue = {'interface':self.mock_xqueue, 'callback_url':'/', 'default_queuename': 'testqueue', 'waittime': 1}
        self.openendedmodule = OpenEndedModule(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 

    def test_message_post(self):
        get = {'feedback': 'feedback text',
                'submission_id': '1',
                'grader_id': '1',
                'score': 3}
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)
        student_info = {'anonymous_student_id': test_system.anonymous_student_id,
                'submission_time': qtime}
        contents = {
                'feedback': get['feedback'],
                'submission_id': int(get['submission_id']),
                'grader_id': int(get['grader_id']),
                'score': get['score'],
                'student_info': json.dumps(student_info)
                }

        result = self.openendedmodule.message_post(get, test_system)
        self.assertTrue(result['success'])
        # make sure it's actually sending something we want to the queue
        self.mock_xqueue.send_to_queue.assert_called_with(body = json.dumps(contents), header=ANY)
        
        state = json.loads(self.openendedmodule.get_instance_state())
        self.assertIsNotNone(state['state'], OpenEndedModule.DONE)

    def test_send_to_grader(self):
        submission = "This is a student submission"
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)
        student_info = {'anonymous_student_id': test_system.anonymous_student_id,
                'submission_time': qtime}
        contents = self.openendedmodule.payload.copy()
        contents.update({ 
            'student_info': json.dumps(student_info),
            'student_response': submission, 
            'max_score': self.max_score
            })
        result = self.openendedmodule.send_to_grader(submission, test_system)
        self.assertTrue(result)
        self.mock_xqueue.send_to_queue.assert_called_with(body = json.dumps(contents), header=ANY)

    def update_score_single(self):
        self.openendedmodule.new_history_entry("New Entry")
        score_msg = { 
                'correct': True,
                'score': 4,
                'msg' : 'Grader Message',
                'feedback': "Grader Feedback"
                }
        get = {'queuekey': "abcd",
                'xqueue_body': score_msg}
        self.openendedmodule.update_score(get, test_system)

    def update_score_single(self):
        self.openendedmodule.new_history_entry("New Entry")
        feedback = {
                "success": True,
                "feedback": "Grader Feedback"
                }
        score_msg = { 
                'correct': True,
                'score': 4,
                'msg' : 'Grader Message',
                'feedback': json.dumps(feedback),
                'grader_type': 'IN',
                'grader_id': '1',
                'submission_id': '1',
                'success': True,
                'rubric_scores': [0],
                'rubric_scores_complete': True,
                'rubric_xml': etree.tostring(self.rubric)
                }
        get = {'queuekey': "abcd",
                'xqueue_body': json.dumps(score_msg)}
        self.openendedmodule.update_score(get, test_system)

    def test_latest_post_assessment(self):
        self.update_score_single()
        assessment = self.openendedmodule.latest_post_assessment(test_system)
        self.assertFalse(assessment == '')
        # check for errors
        self.assertFalse('errors' in assessment)

    def test_update_score(self):
        self.update_score_single()
        score = self.openendedmodule.latest_score()
        self.assertEqual(score, 4)

class CombinedOpenEndedModuleTest(unittest.TestCase):
    location = Location(["i4x", "edX", "open_ended", "combinedopenended",
                         "SampleQuestion"])

    prompt = "<prompt>This is a question prompt</prompt>"
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric></rubric>'''
    max_score = 3

    metadata = {'attempts': '10', 'max_score': max_score}

    static_data = json.dumps({
            'max_attempts': 20,
            'prompt': prompt,
            'rubric': rubric,
            'max_score': max_score, 
            'display_name': 'Name'
            })

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
    descriptor = Mock()

    def setUp(self):
        self.combinedoe = CombinedOpenEndedModule(test_system, self.location, self.definition, self.descriptor, self.static_data, metadata=self.metadata)

    def test_get_tag_name(self):
        name = self.combinedoe.get_tag_name("<t>Tag</t>")
        self.assertEqual(name, "t")

    def test_get_last_response(self):
        response_dict = self.combinedoe.get_last_response(0)
        self.assertEqual(response_dict['type'], "selfassessment")
        self.assertEqual(response_dict['max_score'], self.max_score)
        self.assertEqual(response_dict['state'], CombinedOpenEndedModule.INITIAL)

    def test_update_task_states(self):
        changed = self.combinedoe.update_task_states()
        self.assertFalse(changed)

        current_task = self.combinedoe.current_task
        current_task.change_state(CombinedOpenEndedModule.DONE)
        changed = self.combinedoe.update_task_states()

        self.assertTrue(changed)


