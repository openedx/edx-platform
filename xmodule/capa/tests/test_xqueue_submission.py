"""
Unit tests for the XQueueInterfaceSubmission class.
"""
import json
import pytest
from unittest.mock import Mock, patch
from xmodule.capa.xqueue_submission import XQueueInterfaceSubmission
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds


@pytest.fixture
def xqueue_service():
    """
    Fixture that returns an instance of XQueueInterfaceSubmission.
    """
    location = BlockUsageLocator(
        CourseLocator("test_org", "test_course", "test_run"),
        "problem",
        "ExampleProblem"
    )
    block = Mock(scope_ids=ScopeIds('user1', 'problem', location, location))
    block.max_score = Mock(return_value=10)
    return XQueueInterfaceSubmission(block)


def test_get_submission_params(xqueue_service):
    """
    Test extracting item data from an xqueue submission.
    """
    header = json.dumps({
        'lms_callback_url': 'http://example.com/callback',
        'queue_name': 'default'
    })
    payload = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'test.py'})
    })

    student_item, student_answer, queue_name, grader_file_name, points_possible = (
        xqueue_service.get_submission_params(header, payload)
    )

    assert student_item == {
        'item_id': 'block-v1:test_org+test_course+test_run+type@problem+block@ExampleProblem',
        'item_type': 'problem',
        'course_id': 'course-v1:test_org+test_course+test_run',
        'student_id': 'student_id'
    }
    assert student_answer == 'student_answer'
    assert queue_name == 'default'
    assert grader_file_name == 'test.py'
    assert points_possible == 10


@pytest.mark.django_db
@patch('submissions.api.create_external_grader_detail')
def test_send_to_submission(mock_create_external_grader_detail, xqueue_service):
    """
    Test sending a submission to the grading system.
    """
    header = json.dumps({
        'lms_callback_url': (
            'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/5/'
            'block-v1:test_org+test_course+test_run+type@problem+block@ExampleProblem/'
        ),
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'test.py'})
    })

    mock_response = {"submission": "mock_submission"}
    mock_create_external_grader_detail.return_value = mock_response

    result = xqueue_service.send_to_submission(header, body)

    assert result == mock_response
    mock_create_external_grader_detail.assert_called_once_with(
        {
            'item_id': 'block-v1:test_org+test_course+test_run+type@problem+block@ExampleProblem',
            'item_type': 'problem',
            'course_id': 'course-v1:test_org+test_course+test_run',
            'student_id': 'student_id'
        },
        'student_answer',
        queue_name='default',
        grader_file_name='test.py',
        points_possible=10,
        files=None
    )


@pytest.mark.django_db
@patch('submissions.api.create_external_grader_detail')
def test_send_to_submission_with_missing_fields(mock_create_external_grader_detail, xqueue_service):
    """
    Test send_to_submission with missing required fields.
    """
    header = json.dumps({
        'lms_callback_url': (
            'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/5/'
            'block@item_id/'
        )
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'grader_payload': json.dumps({'grader': 'test.py'})
    })

    result = xqueue_service.send_to_submission(header, body)

    assert "error" in result
    assert "Validation error" in result["error"]
    mock_create_external_grader_detail.assert_not_called()
