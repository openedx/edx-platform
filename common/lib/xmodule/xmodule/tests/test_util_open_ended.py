import json
from StringIO import StringIO

from xmodule.modulestore.xml import XMLModuleStore
from xmodule.tests import DATA_DIR


OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'blah/',
    'username': 'incorrect',
    'password': 'incorrect',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller'
}

S3_INTERFACE = {
    'access_key': "",
    'secret_access_key': "",
    "storage_bucket_name": "",
}


class MockS3Key(object):
    """
    Mock an S3 Key object from boto.  Used for file upload testing.
    """
    def __init__(self, bucket):
        pass

    def set_metadata(self, key, value):
        setattr(self, key, value)

    def set_contents_from_file(self, fileobject):
        self.data = fileobject.read()

    def set_acl(self, acl):
        self.set_metadata("acl", acl)

    def generate_url(self, timeout):
        return "http://www.edx.org/sample_url"


class MockS3Connection(object):
    """
    Mock boto S3Connection for testing image uploads.
    """
    def __init__(self, access_key, secret_key, **kwargs):
        """
        Mock the init call.  S3Connection has a lot of arguments, but we don't need them.
        """
        pass

    def create_bucket(self, bucket_name, **kwargs):
        return "edX Bucket"

    def lookup(self, bucket_name):
        return None


class MockUploadedFile(object):
    """
    Create a mock uploaded file for image submission tests.
    value - String data to place into the mock file.
    return - A StringIO object that behaves like a file.
    """
    def __init__(self, name, value):
        self.mock_file = StringIO()
        self.mock_file.write(value)
        self.name = name

    def seek(self, index):
        return self.mock_file.seek(index)

    def read(self):
        return self.mock_file.read()


class DummyModulestore(object):
    """
    A mixin that allows test classes to have convenience functions to get a module given a location
    """

    def get_module_system(self, descriptor):
        raise NotImplementedError("Sub-tests must specify how to generate a module-system")

    def setup_modulestore(self, name):
        # pylint: disable=attribute-defined-outside-init
        self.modulestore = XMLModuleStore(DATA_DIR, source_dirs=[name])

    def get_course(self, _):
        """Get a test course by directory name.  If there's more than one, error."""
        courses = self.modulestore.get_courses()
        return courses[0]

    def get_module_from_location(self, usage_key):
        descriptor = self.modulestore.get_item(usage_key, depth=None)
        descriptor.xmodule_runtime = self.get_module_system(descriptor)
        return descriptor


def serialize_child_history(task_state):
    """
    To json serialize feedback and post_assessment in child_history of task state.
    """
    child_history = task_state.get("child_history", [])
    for i, attempt in enumerate(child_history):
        if "post_assessment" in attempt:
            if "feedback" in attempt["post_assessment"]:
                attempt["post_assessment"]["feedback"] = json.dumps(attempt["post_assessment"].get("feedback"))
            task_state["child_history"][i]["post_assessment"] = json.dumps(attempt["post_assessment"])


def serialize_open_ended_instance_state(json_str):
    """
    To json serialize task_states and old_task_states in instance state.
    """
    json_data = json.loads(json_str)
    task_states = json_data.get('task_states', [])
    for i, task_state in enumerate(task_states):
        serialize_child_history(task_state)
        json_data['task_states'][i] = json.dumps(task_state)

    old_task_states = json_data.get('old_task_states', [])
    for i, old_task in enumerate(old_task_states):
        for j, task_state in enumerate(old_task):
            old_task[j] = json.dumps(task_state)
        json_data['old_task_states'][i] = old_task

    return json.dumps(json_data)


# Task state for a module with self assessment then instructor assessment.
TEST_STATE_SA_IN = ["{\"child_created\": false, \"child_attempts\": 2, \"version\": 1, \"child_history\": [{\"answer\": \"However venture pursuit he am mr cordial. Forming musical am hearing studied be luckily. Ourselves for determine attending how led gentleman sincerity. Valley afford uneasy joy she thrown though bed set. In me forming general prudent on country carried. Behaved an or suppose justice. Seemed whence how son rather easily and change missed. Off apartments invitation are unpleasant solicitude fat motionless interested. Hardly suffer wisdom wishes valley as an. As friendship advantages resolution it alteration stimulated he or increasing. \\r<br><br>Now led tedious shy lasting females off. Dashwood marianne in of entrance be on wondered possible building. Wondered sociable he carriage in speedily margaret. Up devonshire of he thoroughly insensible alteration. An mr settling occasion insisted distance ladyship so. Not attention say frankness intention out dashwoods now curiosity. Stronger ecstatic as no judgment daughter speedily thoughts. Worse downs nor might she court did nay forth these. \", \"post_assessment\": \"[3, 3, 2, 2, 2]\", \"score\": 12}, {\"answer\": \"Delightful remarkably mr on announcing themselves entreaties favourable. About to in so terms voice at. Equal an would is found seems of. The particular friendship one sufficient terminated frequently themselves. It more shed went up is roof if loud case. Delay music in lived noise an. Beyond genius really enough passed is up. \\r<br><br>John draw real poor on call my from. May she mrs furnished discourse extremely. Ask doubt noisy shade guest did built her him. Ignorant repeated hastened it do. Consider bachelor he yourself expenses no. Her itself active giving for expect vulgar months. Discovery commanded fat mrs remaining son she principle middleton neglected. Be miss he in post sons held. No tried is defer do money scale rooms. \", \"post_assessment\": \"[3, 3, 2, 2, 2]\", \"score\": 12}], \"max_score\": 12, \"child_state\": \"done\"}", "{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"However venture pursuit he am mr cordial. Forming musical am hearing studied be luckily. Ourselves for determine attending how led gentleman sincerity. Valley afford uneasy joy she thrown though bed set. In me forming general prudent on country carried. Behaved an or suppose justice. Seemed whence how son rather easily and change missed. Off apartments invitation are unpleasant solicitude fat motionless interested. Hardly suffer wisdom wishes valley as an. As friendship advantages resolution it alteration stimulated he or increasing. \\r<br><br>Now led tedious shy lasting females off. Dashwood marianne in of entrance be on wondered possible building. Wondered sociable he carriage in speedily margaret. Up devonshire of he thoroughly insensible alteration. An mr settling occasion insisted distance ladyship so. Not attention say frankness intention out dashwoods now curiosity. Stronger ecstatic as no judgment daughter speedily thoughts. Worse downs nor might she court did nay forth these. \", \"post_assessment\": \"{\\\"submission_id\\\": 1460, \\\"score\\\": 12, \\\"feedback\\\": \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 5413, \\\"grader_type\\\": \\\"IN\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>\\\\nIdeas\\\\n</description><score>3</score><option points='0'>\\\\nDifficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.\\\\n</option><option points='1'>\\\\nAttempts a main idea.  Sometimes loses focus or ineffectively displays focus.\\\\n</option><option points='2'>\\\\nPresents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.\\\\n</option><option points='3'>\\\\nPresents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.\\\\n</option></category><category><description>\\\\nContent\\\\n</description><score>3</score><option points='0'>\\\\nIncludes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.\\\\n</option><option points='1'>\\\\nIncludes little information and few or no details.  Explores only one or two facets of the topic.\\\\n</option><option points='2'>\\\\nIncludes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.\\\\n</option><option points='3'>\\\\nIncludes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.\\\\n</option></category><category><description>\\\\nOrganization\\\\n</description><score>2</score><option points='0'>\\\\nIdeas organized illogically, transitions weak, and response difficult to follow.\\\\n</option><option points='1'>\\\\nAttempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.\\\\n</option><option points='2'>\\\\nIdeas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.\\\\n</option></category><category><description>\\\\nStyle\\\\n</description><score>2</score><option points='0'>\\\\nContains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.\\\\n</option><option points='1'>\\\\nContains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).\\\\n</option><option points='2'>\\\\nIncludes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.\\\\n</option></category><category><description>\\\\nVoice\\\\n</description><score>2</score><option points='0'>\\\\nDemonstrates language and tone that may be inappropriate to task and reader.\\\\n</option><option points='1'>\\\\nDemonstrates an attempt to adjust language and tone to task and reader.\\\\n</option><option points='2'>\\\\nDemonstrates effective adjustment of language and tone to task and reader.\\\\n</option></category></rubric>\\\"}\", \"score\": 12}, {\"answer\": \"Delightful remarkably mr on announcing themselves entreaties favourable. About to in so terms voice at. Equal an would is found seems of. The particular friendship one sufficient terminated frequently themselves. It more shed went up is roof if loud case. Delay music in lived noise an. Beyond genius really enough passed is up. \\r<br><br>John draw real poor on call my from. May she mrs furnished discourse extremely. Ask doubt noisy shade guest did built her him. Ignorant repeated hastened it do. Consider bachelor he yourself expenses no. Her itself active giving for expect vulgar months. Discovery commanded fat mrs remaining son she principle middleton neglected. Be miss he in post sons held. No tried is defer do money scale rooms. \", \"post_assessment\": \"{\\\"submission_id\\\": 1462, \\\"score\\\": 12, \\\"feedback\\\": \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 5418, \\\"grader_type\\\": \\\"IN\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>\\\\nIdeas\\\\n</description><score>3</score><option points='0'>\\\\nDifficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.\\\\n</option><option points='1'>\\\\nAttempts a main idea.  Sometimes loses focus or ineffectively displays focus.\\\\n</option><option points='2'>\\\\nPresents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.\\\\n</option><option points='3'>\\\\nPresents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.\\\\n</option></category><category><description>\\\\nContent\\\\n</description><score>3</score><option points='0'>\\\\nIncludes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.\\\\n</option><option points='1'>\\\\nIncludes little information and few or no details.  Explores only one or two facets of the topic.\\\\n</option><option points='2'>\\\\nIncludes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.\\\\n</option><option points='3'>\\\\nIncludes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.\\\\n</option></category><category><description>\\\\nOrganization\\\\n</description><score>2</score><option points='0'>\\\\nIdeas organized illogically, transitions weak, and response difficult to follow.\\\\n</option><option points='1'>\\\\nAttempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.\\\\n</option><option points='2'>\\\\nIdeas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.\\\\n</option></category><category><description>\\\\nStyle\\\\n</description><score>2</score><option points='0'>\\\\nContains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.\\\\n</option><option points='1'>\\\\nContains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).\\\\n</option><option points='2'>\\\\nIncludes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.\\\\n</option></category><category><description>\\\\nVoice\\\\n</description><score>2</score><option points='0'>\\\\nDemonstrates language and tone that may be inappropriate to task and reader.\\\\n</option><option points='1'>\\\\nDemonstrates an attempt to adjust language and tone to task and reader.\\\\n</option><option points='2'>\\\\nDemonstrates effective adjustment of language and tone to task and reader.\\\\n</option></category></rubric>\\\"}\", \"score\": 12}], \"max_score\": 12, \"child_state\": \"post_assessment\"}"]

# Mock instance state.  Should receive a score of 15.
MOCK_INSTANCE_STATE = r"""{"ready_to_reset": false, "skip_spelling_checks": true, "current_task_number": 1, "weight": 5.0, "graceperiod": "1 day 12 hours 59 minutes 59 seconds", "graded": "True", "task_states": ["{\"child_created\": false, \"child_attempts\": 4, \"version\": 1, \"child_history\": [{\"answer\": \"After 24 hours, remove the samples from the containers and rinse each sample with distilled water.\\r\\nAllow the samples to sit and dry for 30 minutes.\\r\\nDetermine the mass of each sample.\\r\\nThe students\\u2019 data are recorded in the table below.\\r\\n\\r\\nStarting Mass (g)\\tEnding Mass (g)\\tDifference in Mass (g)\\r\\nMarble\\t 9.8\\t 9.4\\t\\u20130.4\\r\\nLimestone\\t10.4\\t 9.1\\t\\u20131.3\\r\\nWood\\t11.2\\t11.2\\t 0.0\\r\\nPlastic\\t 7.2\\t 7.1\\t\\u20130.1\\r\\nAfter reading the\", \"post_assessment\": \"[3]\", \"score\": 3}, {\"answer\": \"To replicate the experiment, the procedure would require more detail. One piece of information that is omitted is the amount of vinegar used in the experiment. It is also important to know what temperature the experiment was kept at during the 24 hours. Finally, the procedure needs to include details about the experiment, for example if the whole sample must be submerged.\", \"post_assessment\": \"[3]\", \"score\": 3}, {\"answer\": \"e the mass of four different samples.\\r\\nPour vinegar in each of four separate, but identical, containers.\\r\\nPlace a sample of one material into one container and label. Repeat with remaining samples, placing a single sample into a single container.\\r\\nAfter 24 hours, remove the samples from the containers and rinse each sample with distilled water.\\r\\nAllow the samples to sit and dry for 30 minutes.\\r\\nDetermine the mass of each sample.\\r\\nThe students\\u2019 data are recorded in the table below.\\r\\n\", \"post_assessment\": \"[3]\", \"score\": 3}, {\"answer\": \"\", \"post_assessment\": \"[3]\", \"score\": 3}], \"max_score\": 3, \"child_state\": \"done\"}", "{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"The students\\u2019 data are recorded in the table below.\\r\\n\\r\\nStarting Mass (g)\\tEnding Mass (g)\\tDifference in Mass (g)\\r\\nMarble\\t 9.8\\t 9.4\\t\\u20130.4\\r\\nLimestone\\t10.4\\t 9.1\\t\\u20131.3\\r\\nWood\\t11.2\\t11.2\\t 0.0\\r\\nPlastic\\t 7.2\\t 7.1\\t\\u20130.1\\r\\nAfter reading the group\\u2019s procedure, describe what additional information you would need in order to replicate the expe\", \"post_assessment\": \"{\\\"submission_id\\\": 3097, \\\"score\\\": 0, \\\"feedback\\\": \\\"{\\\\\\\"spelling\\\\\\\": \\\\\\\"Spelling: Ok.\\\\\\\", \\\\\\\"grammar\\\\\\\": \\\\\\\"Grammar: More grammar errors than average.\\\\\\\", \\\\\\\"markup-text\\\\\\\": \\\\\\\"the students data are recorded in the <bg>table below . starting mass</bg> g ending mass g difference in mass g marble . . . limestone . . . wood . . . plastic . . . after reading the groups <bg>procedure , describe what additional</bg> information you would need in order to replicate the <bs>expe</bs>\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 3233, \\\"grader_type\\\": \\\"ML\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Response Quality</description><score>0</score><option points='0'>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option><option points='1'>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option><option points='2'>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option><option points='3'>The response is correct, complete, and contains evidence of higher-order thinking.</option></category></rubric>\\\"}\", \"score\": 0}, {\"answer\": \"After 24 hours, remove the samples from the containers and rinse each sample with distilled water.\\r\\nAllow the samples to sit and dry for 30 minutes.\\r\\nDetermine the mass of each sample.\\r\\nThe students\\u2019 data are recorded in the table below.\\r\\n\\r\\nStarting Mass (g)\\tEnding Mass (g)\\tDifference in Mass (g)\\r\\nMarble\\t 9.8\\t 9.4\\t\\u20130.4\\r\\nLimestone\\t10.4\\t 9.1\\t\\u20131.3\\r\\nWood\\t11.2\\t11.2\\t 0.0\\r\\nPlastic\\t 7.2\\t 7.1\\t\\u20130.1\\r\\nAfter reading the\", \"post_assessment\": \"{\\\"submission_id\\\": 3098, \\\"score\\\": 0, \\\"feedback\\\": \\\"{\\\\\\\"spelling\\\\\\\": \\\\\\\"Spelling: Ok.\\\\\\\", \\\\\\\"grammar\\\\\\\": \\\\\\\"Grammar: Ok.\\\\\\\", \\\\\\\"markup-text\\\\\\\": \\\\\\\"after hours , remove the samples from the containers and rinse each sample with distilled water . allow the samples to sit and dry for minutes . determine the mass of each sample . the students data are recorded in the <bg>table below . starting mass</bg> g ending mass g difference in mass g marble . . . limestone . . . wood . . . plastic . . . after reading the\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 3235, \\\"grader_type\\\": \\\"ML\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Response Quality</description><score>0</score><option points='0'>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option><option points='1'>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option><option points='2'>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option><option points='3'>The response is correct, complete, and contains evidence of higher-order thinking.</option></category></rubric>\\\"}\", \"score\": 0}, {\"answer\": \"To replicate the experiment, the procedure would require more detail. One piece of information that is omitted is the amount of vinegar used in the experiment. It is also important to know what temperature the experiment was kept at during the 24 hours. Finally, the procedure needs to include details about the experiment, for example if the whole sample must be submerged.\", \"post_assessment\": \"{\\\"submission_id\\\": 3099, \\\"score\\\": 3, \\\"feedback\\\": \\\"{\\\\\\\"spelling\\\\\\\": \\\\\\\"Spelling: Ok.\\\\\\\", \\\\\\\"grammar\\\\\\\": \\\\\\\"Grammar: Ok.\\\\\\\", \\\\\\\"markup-text\\\\\\\": \\\\\\\"to replicate the experiment , the procedure would require <bg>more detail . one</bg> piece of information <bg>that is omitted is the</bg> amount of vinegar used in the experiment . it is also important to know what temperature the experiment was kept at during the hours . finally , the procedure needs to include details about the experiment , for example if the whole sample must be submerged .\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 3237, \\\"grader_type\\\": \\\"ML\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Response Quality</description><score>3</score><option points='0'>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option><option points='1'>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option><option points='2'>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option><option points='3'>The response is correct, complete, and contains evidence of higher-order thinking.</option></category></rubric>\\\"}\", \"score\": 3}, {\"answer\": \"e the mass of four different samples.\\r\\nPour vinegar in each of four separate, but identical, containers.\\r\\nPlace a sample of one material into one container and label. Repeat with remaining samples, placing a single sample into a single container.\\r\\nAfter 24 hours, remove the samples from the containers and rinse each sample with distilled water.\\r\\nAllow the samples to sit and dry for 30 minutes.\\r\\nDetermine the mass of each sample.\\r\\nThe students\\u2019 data are recorded in the table below.\\r\\n\", \"post_assessment\": \"{\\\"submission_id\\\": 3100, \\\"score\\\": 0, \\\"feedback\\\": \\\"{\\\\\\\"spelling\\\\\\\": \\\\\\\"Spelling: Ok.\\\\\\\", \\\\\\\"grammar\\\\\\\": \\\\\\\"Grammar: Ok.\\\\\\\", \\\\\\\"markup-text\\\\\\\": \\\\\\\"e the mass of four different samples . pour vinegar in <bg>each of four separate</bg> , but identical , containers . place a sample of one material into one container and label . repeat with remaining samples , placing a single sample into a single container . after hours , remove the samples from the containers and rinse each sample with distilled water . allow the samples to sit and dry for minutes . determine the mass of each sample . the students data are recorded in the table below . \\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 3239, \\\"grader_type\\\": \\\"ML\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Response Quality</description><score>0</score><option points='0'>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option><option points='1'>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option><option points='2'>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option><option points='3'>The response is correct, complete, and contains evidence of higher-order thinking.</option></category></rubric>\\\"}\", \"score\": 0}, {\"answer\": \"\", \"post_assessment\": \"{\\\"submission_id\\\": 3101, \\\"score\\\": 0, \\\"feedback\\\": \\\"{\\\\\\\"spelling\\\\\\\": \\\\\\\"Spelling: Ok.\\\\\\\", \\\\\\\"grammar\\\\\\\": \\\\\\\"Grammar: Ok.\\\\\\\", \\\\\\\"markup-text\\\\\\\": \\\\\\\"invalid essay .\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 3241, \\\"grader_type\\\": \\\"ML\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Response Quality</description><score>0</score><option points='0'>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option><option points='1'>The response is a marginal answer to the question.  It may contain some elements of a proficient response, but it is inaccurate or incomplete.</option><option points='2'>The response is a proficient answer to the question.  It is generally correct, although it may contain minor inaccuracies.  There is limited evidence of higher-order thinking.</option><option points='3'>The response is correct, complete, and contains evidence of higher-order thinking.</option></category></rubric>\\\"}\", \"score\": 0}], \"max_score\": 3, \"child_state\": \"done\"}"], "attempts": "10000", "student_attempts": 0, "due": null, "state": "done", "accept_file_upload": false, "display_name": "Science Question -- Machine Assessed"}"""

# Instance state. To test the rubric scores are consistent. Should receive a score of 15.
INSTANCE_INCONSISTENT_STATE = serialize_open_ended_instance_state("""
{ "accept_file_upload" : false,
  "attempts" : "10000",
  "current_task_number" : 1,
  "display_name" : "Science Question -- Machine Assessed",
  "due" : null,
  "graceperiod" : "1 day 12 hours 59 minutes 59 seconds",
  "graded" : "True",
  "ready_to_reset" : false,
  "skip_spelling_checks" : true,
  "state" : "done",
  "student_attempts" : 0,
  "task_states" : [ { "child_attempts" : 4,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : [ 3 ],
              "score" : 1
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : [ 3 ],
              "score" : 1
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : [ 3 ],
              "score" : 1
            },
            { "answer" : "",
              "post_assessment" : [ 3 ],
              "score" : 1
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      },
      { "child_attempts" : 0,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: More grammar errors than average.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3233,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3097,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3235,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3098,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3237,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>3</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 2,
                  "submission_id" : 3099,
                  "success" : true
                },
              "score" : 2
            },
            { "answer" : "Student answer 4th attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3239,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3100,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "invalid essay .",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3241,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3101,
                  "success" : true
                },
              "score" : 0
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      }
    ],
  "weight" : 5.0
}
    """)

# Instance state. Should receive a score of 10 if grader type is PE.
INSTANCE_INCONSISTENT_STATE2 = serialize_open_ended_instance_state("""
{ "accept_file_upload" : false,
  "attempts" : "10000",
  "current_task_number" : 1,
  "display_name" : "Science Question -- Machine Assessed",
  "due" : null,
  "graceperiod" : "1 day 12 hours 59 minutes 59 seconds",
  "graded" : "True",
  "ready_to_reset" : false,
  "skip_spelling_checks" : true,
  "state" : "done",
  "student_attempts" : 0,
  "task_states" : [ { "child_attempts" : 4,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "",
              "post_assessment" : [3],
              "score" : 1
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      },
      { "child_attempts" : 0,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: More grammar errors than average.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3233,
                  "grader_type" : "PE",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3097,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3235,
                  "grader_type" : "PE",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3098,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3237,
                  "grader_type" : "PE",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>5</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 2,
                  "submission_id" : 3099,
                  "success" : true
                },
              "score" : 2
            },
            { "answer" : "Student answer 4th attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3239,
                  "grader_type" : "PE",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3100,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "invalid essay .",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3241,
                  "grader_type" : "PE",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3101,
                  "success" : true
                },
              "score" : 0
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      }
    ],
  "weight" : 5.0
}
    """)

# Instance state. To test score if sum of rubric score is different from score value. Should receive score of 25.
INSTANCE_INCONSISTENT_STATE3 = serialize_open_ended_instance_state("""
{ "accept_file_upload" : false,
  "attempts" : "10000",
  "current_task_number" : 1,
  "display_name" : "Science Question -- Machine Assessed",
  "due" : null,
  "graceperiod" : "1 day 12 hours 59 minutes 59 seconds",
  "graded" : "True",
  "ready_to_reset" : false,
  "skip_spelling_checks" : true,
  "state" : "done",
  "student_attempts" : 0,
  "task_states" : [ { "child_attempts" : 4,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "",
              "post_assessment" : [3],
              "score" : 1
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      },
      { "child_attempts" : 0,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: More grammar errors than average.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3233,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>2</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3097,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3235,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3098,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3237,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>5</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 2,
                  "submission_id" : 3099,
                  "success" : true
                },
              "score" : 2
            },
            { "answer" : "Student answer 4th attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3239,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3100,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "invalid essay .",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3241,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3101,
                  "success" : true
                },
              "score" : 0
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      }
    ],
  "weight" : 5.0
}
""")

# Instance state. To test score if old task states are available. Should receive a score of 15.
INSTANCE_INCONSISTENT_STATE4 = serialize_open_ended_instance_state("""
{ "accept_file_upload" : false,
  "attempts" : "10000",
  "current_task_number" : 0,
  "display_name" : "Science Question -- Machine Assessed",
  "due" : null,
  "graceperiod" : "1 day 12 hours 59 minutes 59 seconds",
  "graded" : "True",
  "old_task_states" : [ [ { "child_attempts" : 4,
          "child_created" : false,
          "child_history" : [ { "answer" : "Student answer 1st attempt.",
                "post_assessment" : "[3]",
                "score" : 1
              },
              { "answer" : "Student answer 2nd attempt.",
                "post_assessment" : "[3]",
                "score" : 1
              },
              { "answer" : "Student answer 3rd attempt.",
                "post_assesssment" : "[3]",
                "score" : 1
              },
              { "answer" : "",
                "post_assessment" : "[3]",
                "score" : 1
              }
            ],
          "child_state" : "done",
          "max_score" : 3,
          "version" : 1
        } ] ],
  "ready_to_reset" : false,
  "skip_spelling_checks" : true,
  "state" : "assessing",
  "student_attempts" : 0,
  "task_states" : [ { "child_attempts" : 4,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "",
              "post_assessment" : [3],
              "score" : 1
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "stored_answer" : null,
        "version" : 1
      },
      { "child_attempts" : 0,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: More grammar errors than average.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3233,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3097,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3235,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3098,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3237,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>3</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 2,
                  "submission_id" : 3099,
                  "success" : true
                },
              "score" : 2
            },
            { "answer" : "Student answer 4th attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3239,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3100,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "invalid essay .",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3241,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3101,
                  "success" : true
                },
              "score" : 0
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      }
    ],
  "weight" : 5.0
}
""")

# Instance state. To test score if rubric scores are available but score is missing. Should receive a score of 15.
INSTANCE_INCONSISTENT_STATE5 = serialize_open_ended_instance_state("""
{ "accept_file_upload" : false,
  "attempts" : "10000",
  "current_task_number" : 1,
  "display_name" : "Science Question -- Machine Assessed",
  "due" : null,
  "graceperiod" : "1 day 12 hours 59 minutes 59 seconds",
  "graded" : "True",
  "ready_to_reset" : false,
  "skip_spelling_checks" : true,
  "state" : "done",
  "student_attempts" : 0,
  "task_states" : [ { "child_attempts" : 4,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : [3],
              "score" : 1
            },
            { "answer" : "",
              "post_assessment" : [3],
              "score" : 1
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      },
      { "child_attempts" : 0,
        "child_created" : false,
        "child_history" : [ { "answer" : "Student answer 1st attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: More grammar errors than average.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3233,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3097,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 2nd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3235,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3098,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "Student answer 3rd attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3237,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>3</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 2,
                  "submission_id" : 3099,
                  "success" : true
                }
            },
            { "answer" : "Student answer 4th attempt.",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "valid essay",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3239,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3100,
                  "success" : true
                },
              "score" : 0
            },
            { "answer" : "",
              "post_assessment" : { "feedback" : { "grammar" : "Grammar: Ok.",
                      "markup-text" : "invalid essay .",
                      "spelling" : "Spelling: Ok."
                    },
                  "grader_id" : 3241,
                  "grader_type" : "ML",
                  "rubric_scores_complete" : true,
                  "rubric_xml" : "<rubric><category><description>Response Quality</description><score>0</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                  "score" : 0,
                  "submission_id" : 3101,
                  "success" : true
                },
              "score" : 0
            }
          ],
        "child_state" : "done",
        "max_score" : 3,
        "version" : 1
      }
    ],
  "weight" : 5.0
}
""")


# State Initial

STATE_INITIAL = serialize_open_ended_instance_state("""
{
    "ready_to_reset": false,
    "skip_spelling_checks": false,
    "current_task_number": 0,
    "old_task_states": [],
    "weight": 1,
    "task_states": [
        {
            "child_attempts" : 1,
            "child_created" : false,
            "child_history" : [],
            "child_state" : "done",
            "max_score" : 3,
            "version" : 1
        },
        {
            "child_created": false,
            "child_attempts": 0,
            "stored_answer": "A stored answer.",
            "version": 1,
            "child_history": [],
            "max_score": 3,
            "child_state": "initial"
        }
    ],
    "graded": true,
    "student_attempts": 0,
    "required_peer_grading": 3,
    "state": "initial",
    "accept_file_upload": false,
    "min_to_calibrate": 3,
    "max_to_calibrate": 6,
    "display_name": "Open Response Assessment",
    "peer_grader_count": 3,
    "max_attempts": 1
}""")

STATE_ACCESSING = serialize_open_ended_instance_state("""
{
    "ready_to_reset": false,
    "skip_spelling_checks": false,
    "current_task_number": 0,
    "old_task_states": [],
    "weight": 1,
    "task_states": [
        {
            "child_attempts" : 1,
            "child_created" : false,
            "child_history": [
                {
                    "answer": "Here is an answer."
                }
            ],
            "child_state" : "done",
            "max_score" : 3,
            "version" : 1
        },
        {
            "child_created": false,
            "child_attempts": 0,
            "stored_answer": null,
            "version": 1,
            "child_history": [
                {
                    "answer": "Here is an answer."
                }
            ],
            "max_score": 3,
            "child_state": "assessing"
        }
    ],
    "graded": true,
    "student_attempts": 0,
    "required_peer_grading": 3,
    "state": "assessing",
    "accept_file_upload": false,
    "min_to_calibrate": 3,
    "max_to_calibrate": 6,
    "display_name": "Open Response Assessment",
    "peer_grader_count": 3,
    "max_attempts": 1
}""")

STATE_POST_ASSESSMENT = serialize_open_ended_instance_state("""
{
    "ready_to_reset": false,
    "skip_spelling_checks": false,
    "current_task_number": 0,
    "old_task_states": [],
    "weight": 1,
    "task_states": [
        {
            "child_attempts" : 1,
            "child_created" : false,
            "child_history": [
                {
                    "answer": "Here is an answer."
                }
            ],
            "child_state" : "done",
            "max_score" : 3,
            "version" : 1
        },
        {
            "child_created": false,
            "child_attempts": 0,
            "stored_answer": null,
            "version": 1,
            "child_history": [
                {
                    "answer": "Here is an answer."
                }
            ],
            "max_score": 3,
            "post_assessment": {
                "feedback" : {
                    "grammar" : "Grammar: Ok.",
                    "markup-text" : "valid essay",
                    "spelling" : "Spelling: Ok."
                },
                "grader_id" : 3237,
                "grader_type" : "ML",
                "rubric_scores_complete" : true,
                "rubric_xml" : "<rubric><category><description>Response Quality</description><score>3</score><option points='0'>Category one description.</option><option points='1'>Category two description.</option><option points='2'>Category three description.</option><option points='3'>Category four description.</option></category></rubric>",
                "score" : 2,
                "submission_id" : 3099,
                "success" : true
            },
            "child_state": "post_assessment"
        }
    ],
    "graded": true,
    "student_attempts": 0,
    "required_peer_grading": 3,
    "state": "done",
    "accept_file_upload": false,
    "min_to_calibrate": 3,
    "max_to_calibrate": 6,
    "display_name": "Open Response Assessment",
    "peer_grader_count": 3,
    "max_attempts": 1
}""")

# Task state with self assessment only.
TEST_STATE_SA = ["{\"child_created\": false, \"child_attempts\": 1, \"version\": 1, \"child_history\": [{\"answer\": \"Censorship in the Libraries\\r<br>'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author\\r<br><br>Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.\", \"post_assessment\": \"[3, 3, 2, 2, 2]\", \"score\": 12}], \"max_score\": 12, \"child_state\": \"done\"}", "{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"Censorship in the Libraries\\r<br>'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author\\r<br><br>Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.\", \"post_assessment\": \"{\\\"submission_id\\\": 1461, \\\"score\\\": 12, \\\"feedback\\\": \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 5414, \\\"grader_type\\\": \\\"IN\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>\\\\nIdeas\\\\n</description><score>3</score><option points='0'>\\\\nDifficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.\\\\n</option><option points='1'>\\\\nAttempts a main idea.  Sometimes loses focus or ineffectively displays focus.\\\\n</option><option points='2'>\\\\nPresents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.\\\\n</option><option points='3'>\\\\nPresents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.\\\\n</option></category><category><description>\\\\nContent\\\\n</description><score>3</score><option points='0'>\\\\nIncludes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.\\\\n</option><option points='1'>\\\\nIncludes little information and few or no details.  Explores only one or two facets of the topic.\\\\n</option><option points='2'>\\\\nIncludes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.\\\\n</option><option points='3'>\\\\nIncludes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.\\\\n</option></category><category><description>\\\\nOrganization\\\\n</description><score>2</score><option points='0'>\\\\nIdeas organized illogically, transitions weak, and response difficult to follow.\\\\n</option><option points='1'>\\\\nAttempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.\\\\n</option><option points='2'>\\\\nIdeas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.\\\\n</option></category><category><description>\\\\nStyle\\\\n</description><score>2</score><option points='0'>\\\\nContains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.\\\\n</option><option points='1'>\\\\nContains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).\\\\n</option><option points='2'>\\\\nIncludes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.\\\\n</option></category><category><description>\\\\nVoice\\\\n</description><score>2</score><option points='0'>\\\\nDemonstrates language and tone that may be inappropriate to task and reader.\\\\n</option><option points='1'>\\\\nDemonstrates an attempt to adjust language and tone to task and reader.\\\\n</option><option points='2'>\\\\nDemonstrates effective adjustment of language and tone to task and reader.\\\\n</option></category></rubric>\\\"}\", \"score\": 12}], \"max_score\": 12, \"child_state\": \"post_assessment\"}"]

# Task state with self and then ai assessment.
TEST_STATE_AI = ["{\"child_created\": false, \"child_attempts\": 2, \"version\": 1, \"child_history\": [{\"answer\": \"In libraries, there should not be censorship on materials considering that it's an individual's decision to read what they prefer. There is no appropriate standard on what makes a book offensive to a group, so it should be undetermined as to what makes a book offensive. In a public library, many children, who the books are censored for, are with their parents. Parents should make an independent choice on what they can allow their children to read. Letting society ban a book simply for the use of inappropriate materials is ridiculous. If an author spent time creating a story, it should be appreciated, and should not put on a list of no-nos. If a certain person doesn't like a book's reputation, all they have to do is not read it. Even in school systems, librarians are there to guide kids to read good books. If a child wants to read an inappropriate book, the librarian will most likely discourage him or her not to read it. In my experience, I wanted to read a book that my mother suggested to me, but as I went to the school library it turned out to be a censored book. Some parents believe children should be ignorant about offensive things written in books, but honestly many of the same ideas are exploited to them everyday on television and internet. So trying to shield your child from the bad things may be a great thing, but the efforts are usually failed attempts. It also never occurs to the people censoring the books, that some people can't afford to buy the books they want to read. The libraries, for some, are the main means for getting books. To conclude there is very little reason to ban a book from the shelves. Many of the books banned have important lessons that can be obtained through reading it. If a person doesn't like a book, the simplest thing to do is not to pick it up.\", \"post_assessment\": \"[1, 1]\", \"score\": 2}, {\"answer\": \"This is another response\", \"post_assessment\": \"[1, 1]\", \"score\": 2}], \"max_score\": 2, \"child_state\": \"done\"}", "{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"In libraries, there should not be censorship on materials considering that it's an individual's decision to read what they prefer. There is no appropriate standard on what makes a book offensive to a group, so it should be undetermined as to what makes a book offensive. In a public library, many children, who the books are censored for, are with their parents. Parents should make an independent choice on what they can allow their children to read. Letting society ban a book simply for the use of inappropriate materials is ridiculous. If an author spent time creating a story, it should be appreciated, and should not put on a list of no-nos. If a certain person doesn't like a book's reputation, all they have to do is not read it. Even in school systems, librarians are there to guide kids to read good books. If a child wants to read an inappropriate book, the librarian will most likely discourage him or her not to read it. In my experience, I wanted to read a book that my mother suggested to me, but as I went to the school library it turned out to be a censored book. Some parents believe children should be ignorant about offensive things written in books, but honestly many of the same ideas are exploited to them everyday on television and internet. So trying to shield your child from the bad things may be a great thing, but the efforts are usually failed attempts. It also never occurs to the people censoring the books, that some people can't afford to buy the books they want to read. The libraries, for some, are the main means for getting books. To conclude there is very little reason to ban a book from the shelves. Many of the books banned have important lessons that can be obtained through reading it. If a person doesn't like a book, the simplest thing to do is not to pick it up.\", \"post_assessment\": \"{\\\"submission_id\\\": 6107, \\\"score\\\": 2, \\\"feedback\\\": \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"success\\\": true, \\\"grader_id\\\": 1898718, \\\"grader_type\\\": \\\"IN\\\", \\\"rubric_scores_complete\\\": true, \\\"rubric_xml\\\": \\\"<rubric><category><description>Writing Applications</description><score>1</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>1</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\"}\", \"score\": 2}, {\"answer\": \"This is another response\"}], \"max_score\": 2, \"child_state\": \"assessing\"}"]

# Task state with ai assessment only.
TEST_STATE_AI2 = ["{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"This isn't a real essay, and you should give me a zero on it. \", \"post_assessment\": \"{\\\"submission_id\\\": 18446, \\\"score\\\": [0, 1, 0], \\\"feedback\\\": [\\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"Zero it is! \\\\\\\"}\\\"], \\\"success\\\": true, \\\"grader_id\\\": [1944146, 1943188, 1940991], \\\"grader_type\\\": \\\"PE\\\", \\\"rubric_scores_complete\\\": [true, true, true], \\\"rubric_xml\\\": [\\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\", \\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>1</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\", \\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\"]}\", \"score\": 0}], \"max_score\": 2, \"child_state\": \"post_assessment\"}"]

# Invalid task state with ai assessment.
TEST_STATE_AI2_INVALID = ["{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"This isn't a real essay, and you should give me a zero on it. \", \"post_assessment\": \"{\\\"submission_id\\\": 18446, \\\"score\\\": [0, 1, 0], \\\"feedback\\\": [\\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\", \\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"Zero it is! \\\\\\\"}\\\"], \\\"success\\\": true, \\\"grader_id\\\": [1943188, 1940991], \\\"grader_type\\\": \\\"PE\\\", \\\"rubric_scores_complete\\\": [true, true, true], \\\"rubric_xml\\\": [\\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\", \\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>1</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\", \\\"<rubric><category><description>Writing Applications</description><score>0</score><option points='0'> The essay loses focus, has little information or supporting details, and the organization makes it difficult to follow.</option><option points='1'> The essay presents a mostly unified theme, includes sufficient information to convey the theme, and is generally organized well.</option></category><category><description> Language Conventions </description><score>0</score><option points='0'> The essay demonstrates a reasonable command of proper spelling and grammar. </option><option points='1'> The essay demonstrates superior command of proper spelling and grammar.</option></category></rubric>\\\"]}\", \"score\": 0}], \"max_score\": 2, \"child_state\": \"post_assessment\"}"]

# Self assessment state.
TEST_STATE_SINGLE = ["{\"child_created\": false, \"child_attempts\": 1, \"version\": 1, \"child_history\": [{\"answer\": \"'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author\\r<br><br>Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading. \", \"post_assessment\": \"[3, 3, 2, 2, 2]\", \"score\": 12}], \"max_score\": 12, \"child_state\": \"done\"}"]

# Peer grading state.
TEST_STATE_PE_SINGLE = ["{\"child_created\": false, \"child_attempts\": 0, \"version\": 1, \"child_history\": [{\"answer\": \"Passage its ten led hearted removal cordial. Preference any astonished unreserved mrs. Prosperous understood middletons in conviction an uncommonly do. Supposing so be resolving breakfast am or perfectly. Is drew am hill from mr. Valley by oh twenty direct me so. Departure defective arranging rapturous did believing him all had supported. Family months lasted simple set nature vulgar him. Picture for attempt joy excited ten carried manners talking how. Suspicion neglected he resolving agreement perceived at an. \\r<br><br>Ye on properly handsome returned throwing am no whatever. In without wishing he of picture no exposed talking minutes. Curiosity continual belonging offending so explained it exquisite. Do remember to followed yourself material mr recurred carriage. High drew west we no or at john. About or given on witty event. Or sociable up material bachelor bringing landlord confined. Busy so many in hung easy find well up. So of exquisite my an explained remainder. Dashwood denoting securing be on perceive my laughing so. \\r<br><br>Ought these are balls place mrs their times add she. Taken no great widow spoke of it small. Genius use except son esteem merely her limits. Sons park by do make on. It do oh cottage offered cottage in written. Especially of dissimilar up attachment themselves by interested boisterous. Linen mrs seems men table. Jennings dashwood to quitting marriage bachelor in. On as conviction in of appearance apartments boisterous. \", \"post_assessment\": \"{\\\"submission_id\\\": 1439, \\\"score\\\": [0], \\\"feedback\\\": [\\\"{\\\\\\\"feedback\\\\\\\": \\\\\\\"\\\\\\\"}\\\"], \\\"success\\\": true, \\\"grader_id\\\": [5337], \\\"grader_type\\\": \\\"PE\\\", \\\"rubric_scores_complete\\\": [true], \\\"rubric_xml\\\": [\\\"<rubric><category><description>\\\\nIdeas\\\\n</description><score>0</score><option points='0'>\\\\nDifficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.\\\\n</option><option points='1'>\\\\nAttempts a main idea.  Sometimes loses focus or ineffectively displays focus.\\\\n</option><option points='2'>\\\\nPresents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.\\\\n</option><option points='3'>\\\\nPresents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.\\\\n</option></category><category><description>\\\\nContent\\\\n</description><score>0</score><option points='0'>\\\\nIncludes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.\\\\n</option><option points='1'>\\\\nIncludes little information and few or no details.  Explores only one or two facets of the topic.\\\\n</option><option points='2'>\\\\nIncludes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.\\\\n</option><option points='3'>\\\\nIncludes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.\\\\n</option></category><category><description>\\\\nOrganization\\\\n</description><score>0</score><option points='0'>\\\\nIdeas organized illogically, transitions weak, and response difficult to follow.\\\\n</option><option points='1'>\\\\nAttempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.\\\\n</option><option points='2'>\\\\nIdeas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.\\\\n</option></category><category><description>\\\\nStyle\\\\n</description><score>0</score><option points='0'>\\\\nContains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.\\\\n</option><option points='1'>\\\\nContains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).\\\\n</option><option points='2'>\\\\nIncludes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.\\\\n</option></category><category><description>\\\\nVoice\\\\n</description><score>0</score><option points='0'>\\\\nDemonstrates language and tone that may be inappropriate to task and reader.\\\\n</option><option points='1'>\\\\nDemonstrates an attempt to adjust language and tone to task and reader.\\\\n</option><option points='2'>\\\\nDemonstrates effective adjustment of language and tone to task and reader.\\\\n</option></category></rubric>\\\"]}\", \"score\": 0}], \"max_score\": 12, \"child_state\": \"done\"}"]
