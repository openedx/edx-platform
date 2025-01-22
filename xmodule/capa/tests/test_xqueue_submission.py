import json
import pytest
from unittest.mock import Mock, patch
from django.conf import settings
from xmodule.capa.xqueue_submission import XQueueServiceSubmission, XQueueInterfaceSubmission, extract_item_data
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds


@pytest.fixture
def xqueue_service():
    """Fixture que devuelve un objeto XQueueServiceSubmission configurado para pruebas."""
    location = BlockUsageLocator(CourseLocator("test_org", "test_course", "test_run"), "problem", "ExampleProblem")
    block = Mock(scope_ids=ScopeIds('user1', 'mock_problem', location, location))
    return XQueueServiceSubmission(block)


def test_interface_creation(xqueue_service):
    """Verifica que XQueueServiceSubmission cree un objeto XQueueInterfaceSubmission válido."""
    assert isinstance(xqueue_service.interface, XQueueInterfaceSubmission)


def test_send_callback_generation(xqueue_service):
    """Verifica que send_callback genere una URL de callback válida."""
    usage_id = xqueue_service._block.scope_ids.usage_id
    callback_url = f'courses/{usage_id.context_key}/xqueue/user1/{usage_id}'
    expected_callback = f'{settings.XQUEUE_INTERFACE["url"]}/{callback_url}/score_update'
    assert xqueue_service.send_callback() == expected_callback


def test_default_queue_name(xqueue_service):
    """Verifica que default_queuename retorne un nombre de cola formateado correctamente."""
    course_id = xqueue_service._block.scope_ids.usage_id.context_key
    expected_queue_name = f'{course_id.org}-{course_id.course}'.replace(' ', '_')
    assert xqueue_service.default_queuename == expected_queue_name


def test_extract_item_data():
    """Prueba la extracción de datos de un header y payload proporcionados."""
    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:org+course+run/xqueue/5/block-v1:org+course+run+type@problem+block@item_id/score_update',
    })
    payload = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer'
    })

    student_item, student_answer = extract_item_data(header, payload)
    assert student_item == {
        'item_id': 'item_id',
        'item_type': 'problem',
        'course_id': 'org+course+run',
        'student_id': 'student_id'
    }
    assert student_answer == 'student_answer'


@patch('submissions.api.create_submission')
def test_send_to_submission(mock_create_submission, xqueue_service):
    """Prueba el flujo de envío a submission."""
    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/block@item_id/type@problem',
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer'
    })

    mock_create_submission.return_value = {'submission': 'mock_submission'}
    # Llamada a send_to_submission
    error, msg = xqueue_service.interface.send_to_submission(header, body)
    
    # Afirmaciones
    assert error == 0
    assert msg == "Submission sent successfully"
    mock_create_submission.assert_called_once_with(
        {
            'item_id': 'item_id',
            'item_type': 'problem',
            'course_id': 'test_org+test_course+test_run',
            'student_id': 'student_id'
        },
        'student_answer'
    )
