import json
import pytest
from unittest.mock import Mock, patch
from django.conf import settings
from xmodule.capa.xqueue_submission import XQueueInterfaceSubmission, extract_item_data
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds


@pytest.fixture
def xqueue_service():
    location = BlockUsageLocator(CourseLocator("test_org", "test_course", "test_run"), "problem", "ExampleProblem")
    block = Mock(scope_ids=ScopeIds('user1', 'mock_problem', location, location))
    return XQueueInterfaceSubmission()


def test_extract_item_data():
    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:org+course+run/xqueue/5/block-v1:org+course+run+type@problem+block@item_id/score_update',
    })
    payload = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'example_grader'})
    })

    student_item, student_answer, queue_name, grader = extract_item_data(header, payload)
    assert student_item == {
        'item_id': 'item_id',
        'item_type': 'problem',
        'course_id': 'org+course+run',
        'student_id': 'student_id'
    }
    assert student_answer == 'student_answer'
    assert queue_name == 'default'
    assert grader == 'example_grader'


@patch('submissions.api.create_submission')
def test_send_to_submission(mock_create_submission, xqueue_service):
    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/block@item_id/type@problem',
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'example_grader'})
    })

    mock_create_submission.return_value = {'submission': 'mock_submission'}
    
    result = xqueue_service.send_to_submission(header, body)
    
    # Afirmaciones
    assert 'submission' in result
    assert result['submission'] == 'mock_submission'
    mock_create_submission.assert_called_once_with(
        {
            'item_id': 'item_id',
            'item_type': 'problem',
            'course_id': 'test_org+test_course+test_run',
            'student_id': 'student_id'
        },
        'student_answer',
        queue_name='default',
        grader='example_grader'
    )