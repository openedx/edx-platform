"""
Tests for context processors in philu_overrides
"""

import mock
import pytest
from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse

from lms.djangoapps.philu_overrides.constants import (
    ACTIVATION_ALERT_TYPE,
    ACTIVATION_ERROR_MSG_FORMAT,
    ORG_DETAILS_UPDATE_ALERT,
    ORG_OEF_UPDATE_ALERT
)
from lms.djangoapps.philu_overrides.context_processor import (
    add_nodebb_endpoint,
    get_cdn_link,
    get_global_alert_messages
)
from student.tests.factories import AnonymousUserFactory, UserFactory


@pytest.fixture()
def request_object(db):  # pylint: disable=unused-argument
    request = RequestFactory().get('/dummy_url')
    request.user = UserFactory.create()
    return request

# Tests for get_global_alert_messages context processor

# ACTIVATION_ERROR_MSG Tests


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_activation_error_alert_message_success(request_object):  # pylint: disable=redefined-outer-name
    """
    Test that get_global_alert_messages should return activation error message as the context when:
        - request is not AJAX,
        - user is authenticated,
        - user is inactive,
        - user is not requesting for activation
    """

    request = request_object
    request.user.is_active = False

    expected_global_alert_message = [
        {
            'type': ACTIVATION_ALERT_TYPE,
            'alert': ACTIVATION_ERROR_MSG_FORMAT.format(
                api_endpoint=reverse('resend_activation_email'),
                user_id=request.user.id
            )
        }
    ]

    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_activation_error_alert_message_ajax_failure(request_object):  # pylint: disable=redefined-outer-name
    """
    Test that get_global_alert_messages should NOT return activation error message as the context
    when request is AJAX
    """

    request = request_object
    request.user.is_active = False
    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'  # so request.is_ajax() == True

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_activation_error_alert_message_auth_failure(request_object):  # pylint: disable=redefined-outer-name
    """
    Test that get_global_alert_messages should NOT return activation error message as the context
    when user is unauthenticated
    """

    request = request_object
    request.user = AnonymousUserFactory.create()  # AnonymousUserFactory creates an unauthenticated user
    request.user.is_active = False

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_activation_error_alert_message_active_user_failure(request_object):  # pylint: disable=redefined-outer-name
    """
    Test that get_global_alert_messages should NOT return activation error message as the context
    when user is already active
    """

    request = request_object

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_activation_error_alert_message_activation_url_failure(
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return activation error message as the context
    upon direction to the activation url, i.e. when request.path contains '/activate/'
    """

    request = request_object
    request.user.is_active = False
    request.path = request.path + '/activate/'

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message

# ORG_OEF_UPDATE_ALERT Tests


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_org_oef_update_alert_message_success(
    mock_get_org_oef_update_prompt,
    mock_is_org_oef_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns ORG_OEF_UPDATE_ALERT as the context successfully when:
        - oef_update_prompt = True,
        - org_oef_prompt_available = True
        - request.path contains '/oef/dashboard',
    """

    request = request_object
    request.path = request.path + '/oef/dashboard'

    mock_get_org_oef_update_prompt.return_value = True
    mock_is_org_oef_prompt_available.return_value = True

    expected_global_alert_message = [
        {
            'type': ACTIVATION_ALERT_TYPE,
            'alert': ORG_OEF_UPDATE_ALERT
        }
    ]
    expected_oef_prompt = True

    actual_result = get_global_alert_messages(request)
    actual_global_alert_message = actual_result.get('global_alert_messages')
    actual_oef_prompt = actual_result.get('oef_prompt')

    assert expected_global_alert_message == actual_global_alert_message
    assert expected_oef_prompt == actual_oef_prompt


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_org_oef_update_alert_message_oef_prompt_failure(
    mock_get_org_oef_update_prompt,
    mock_is_org_oef_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_OEF_UPDATE_ALERT as the context when:
    oef_update_prompt = False
    """

    request = request_object
    request.path = request.path + '/oef/dashboard'

    mock_get_org_oef_update_prompt.return_value = False
    mock_is_org_oef_prompt_available.return_value = True

    expected_global_alert_message = []
    expected_oef_prompt = None

    actual_result = get_global_alert_messages(request)
    actual_global_alert_message = actual_result.get('global_alert_messages')
    actual_oef_prompt = actual_result.get('oef_prompt')

    assert expected_global_alert_message == actual_global_alert_message
    assert expected_oef_prompt == actual_oef_prompt


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_org_oef_update_alert_message_oef_available_failure(
    mock_get_org_oef_update_prompt,
    mock_is_org_oef_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_OEF_UPDATE_ALERT as the contex twhen:
    org_oef_prompt_available = False
    """

    request = request_object
    request.path = request.path + '/oef/dashboard'

    mock_get_org_oef_update_prompt.return_value = True
    mock_is_org_oef_prompt_available.return_value = False

    expected_global_alert_message = []
    expected_oef_prompt = None

    actual_result = get_global_alert_messages(request)
    actual_global_alert_message = actual_result.get('global_alert_messages')
    actual_oef_prompt = actual_result.get('oef_prompt')

    assert expected_global_alert_message == actual_global_alert_message
    assert expected_oef_prompt == actual_oef_prompt


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt', mock.Mock())
def test_get_org_oef_update_alert_message_url_failure(
    mock_get_org_oef_update_prompt,
    mock_is_org_oef_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_OEF_UPDATE_ALERT as the context when:
    '/oef/dashboard' is not part of the request url
    """

    request = request_object

    mock_get_org_oef_update_prompt.return_value = True
    mock_is_org_oef_prompt_available.return_value = True

    expected_global_alert_message = []
    expected_oef_prompt = None

    actual_result = get_global_alert_messages(request)
    actual_global_alert_message = actual_result.get('global_alert_messages')
    actual_oef_prompt = actual_result.get('oef_prompt')

    assert expected_global_alert_message == actual_global_alert_message
    assert expected_oef_prompt == actual_oef_prompt

# ORG_DETAILS_UPDATE_ALERT Tests

@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_get_org_details_update_alert_message_success(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns ORG_DETAILS_UPDATE_ALERT as the context successfully when:
        - metric_update_prompt = True,
        - org_detail_prompt_available = True
        - request.path contains '/organization/details/',
    """

    request = request_object
    request.path = request.path + '/organization/details/'

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True

    expected_global_alert_message = [
        {
            'type': ACTIVATION_ALERT_TYPE,
            'alert': ORG_DETAILS_UPDATE_ALERT
        }
    ]

    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_get_org_details_update_alert_message_metric_prompt_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_DETAILS_UPDATE_ALERT as the context when:
    metric_update_prompt = False
    """

    request = request_object
    request.path = request.path + '/organization/details/'

    mock_get_org_metric_update_prompt.return_value = False
    mock_is_org_detail_prompt_available.return_value = True

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_get_org_details_update_alert_message_detail_prompt_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_DETAILS_UPDATE_ALERT as the context when:
    org_detail_prompt_available = False
    """

    request = request_object
    request.path = request.path + '/organization/details/'

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = False

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_get_org_details_update_alert_message_url_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages should NOT return ORG_DETAILS_UPDATE_ALERT as the context when:
    '/organization/details/' is not part of the request url
    """

    request = request_object

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True

    expected_global_alert_message = []
    actual_global_alert_message = get_global_alert_messages(request).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message

# Overlay Message Tests


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_success(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = True when:
        - metric_update_prompt = True,
        - org_detail_prompt_available = True,
        - org_detail_platform_overlay_available = True,
        - request.path does not contain '/oef/dashboard'
        - request.path does not contain '/organization/details/'
    """

    request = request_object

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True
    mock_is_org_detail_platform_overlay_available.return_value = True

    expected_overlay_message = True

    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_metric_prompt_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = None when metric_update_prompt = False
    """

    request = request_object

    mock_get_org_metric_update_prompt.return_value = False
    mock_is_org_detail_prompt_available.return_value = True
    mock_is_org_detail_platform_overlay_available.return_value = True

    expected_overlay_message = None
    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_detail_prompt_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = None when org_detail_prompt_available = False
    """

    request = request_object

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = False
    mock_is_org_detail_platform_overlay_available.return_value = True

    expected_overlay_message = None
    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_platform_overlay_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = None when
    org_detail_platform_overlay_available = False
    """

    request = request_object

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True
    mock_is_org_detail_platform_overlay_available.return_value = False

    expected_overlay_message = None
    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_oef_url_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = None when request.path contains '/oef/dashboard'
    """

    request = request_object
    request.path = request.path + '/oef/dashboard'

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True
    mock_is_org_detail_platform_overlay_available.return_value = True

    expected_overlay_message = None
    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt', mock.Mock())
@mock.patch('lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available')
@mock.patch('lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt')
def test_overlay_message_org_url_failure(
    mock_get_org_metric_update_prompt,
    mock_is_org_detail_prompt_available,
    mock_is_org_detail_platform_overlay_available,
    request_object  # pylint: disable=redefined-outer-name
):
    """
    Test that get_global_alert_messages returns overlay_message = None when request.path contains '/oef/dashboard'
    """

    request = request_object
    request.path = request.path + '/organization/details/'

    mock_get_org_metric_update_prompt.return_value = True
    mock_is_org_detail_prompt_available.return_value = True
    mock_is_org_detail_platform_overlay_available.return_value = True

    expected_overlay_message = None
    actual_overlay_message = get_global_alert_messages(request).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message

# Tests for other context processors


def test_add_nodebb_endpoint():
    request = 'request'
    expected_result = {'nodebb_endpoint': settings.NODEBB_ENDPOINT}
    actual_result = add_nodebb_endpoint(request)
    assert expected_result == actual_result


def test_get_cdn_link():
    request = 'request'
    expected_result = {'cdn_link': settings.CDN_LINK}
    actual_result = get_cdn_link(request)
    assert expected_result == actual_result
