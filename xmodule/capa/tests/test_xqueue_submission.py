"""
Tests for XQueueInterfaceSubmission.
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
    block = Mock(scope_ids=ScopeIds('user1', 'mock_problem', location, location))
    return XQueueInterfaceSubmission()


def test_extract_item_data():
    """
    Test extracting item data from an xqueue submission.
    """
    header = json.dumps({
        'lms_callback_url': (
            'http://example.com/courses/course-v1:org+course+run/xqueue/5/'
            'block-v1:org+course+run+type@problem+block@item_id/score_update'
        ),
    })
    payload = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'test.py'})
    })
    with patch('lms.djangoapps.courseware.models.StudentModule.objects.filter') as mock_filter:
        mock_filter.return_value.first.return_value = Mock(grade=0.85)

        student_item, student_answer, queue_name, grader, score = (
            XQueueInterfaceSubmission().extract_item_data(header, payload)
        )

        assert student_item == {
            'item_id': (
                'block-v1:org+course+run+type@problem+block@item_id'
            ),
            'item_type': 'problem',
            'course_id': 'course-v1:org+course+run',
            'student_id': 'student_id'
        }
        assert student_answer == 'student_answer'
        assert queue_name == 'default'
        assert grader == 'test.py'
        assert score == 0.85


@pytest.mark.django_db
@patch('submissions.api.create_submission')
def test_send_to_submission(mock_create_submission, xqueue_service):
    """
    Test sending a submission to the grading system.
    """
    header = json.dumps({
        'lms_callback_url': (
            'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/5/'
            'block-v1:test_org+test_course+test_run+type@problem+block@item_id/score_update'
        ),
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer',
        'grader_payload': json.dumps({'grader': 'test.py'})
    })

    with patch('lms.djangoapps.courseware.models.StudentModule.objects.filter') as mock_filter:
        mock_filter.return_value.first.return_value = Mock(grade=0.85)

        mock_create_submission.return_value = {'submission': 'mock_submission'}

        # Call send_to_submission
        result = xqueue_service.send_to_submission(header, body)

        # Assertions
        assert 'submission' in result
        assert result['submission'] == 'mock_submission'
        mock_create_submission.assert_called_once_with(
            {
                'item_id': 'block-v1:test_org+test_course+test_run+type@problem+block@item_id',
                'item_type': 'problem',
                'course_id': 'course-v1:test_org+test_course+test_run',
                'student_id': 'student_id'
            },
            'student_answer',
            queue_name='default',
            grader='test.py',
            score=0.85
        )


@pytest.mark.django_db
@patch('submissions.api.create_submission')
def test_send_to_submission_with_missing_fields(mock_create_submission, xqueue_service):
    """
    Test send_to_submission with missing required fields.
    """
    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/5/block@item_id'
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'grader_payload': json.dumps({'grader': 'test.py'})
    })

    # Call send_to_submission
    result = xqueue_service.send_to_submission(header, body)

    # Assertions
    assert "error" in result
    assert "Validation error" in result["error"]
    mock_create_submission.assert_not_called()
