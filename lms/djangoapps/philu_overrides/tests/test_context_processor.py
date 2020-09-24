"""
Tests for context processors in philu_overrides
"""
# pylint: disable=redefined-outer-name

import pytest
from mock import Mock

from lms.djangoapps.philu_overrides.constants import (
    CDN_LINK_DICT,
    NODEBB_END_POINT_DICT,
    ORG_DETAILS_UPDATE_ALERT_MSG_DICT,
    ORG_OEF_UPDATE_ALERT_MSG_DICT
)
from lms.djangoapps.philu_overrides.context_processor import (
    add_nodebb_endpoint,
    get_cdn_link,
    get_global_alert_messages
)
from lms.djangoapps.philu_overrides.helpers import get_activation_alert_error_msg_dict
from student.tests.factories import AnonymousUserFactory, UserFactory


@pytest.fixture()
def request_obj(db, rf):  # pylint: disable=unused-argument
    request = rf.get('/dummy_url')
    request.user = UserFactory.create()
    return request


def _mock_get_global_alert_messages_dependencies(
    mocker,
    is_org_detail_platform_overlay_available_return_value=Mock(),
    is_org_oef_prompt_available_return_value=Mock(),
    get_org_oef_update_prompt_return_value=Mock(),
    is_org_detail_prompt_available_return_value=Mock(),
    get_org_metric_update_prompt_return_value=Mock()
):
    """
    Mock all dependencies of the function 'get_global_alert_messages' at module level
    """
    mocker.patch(
        'lms.djangoapps.philu_overrides.context_processor.is_org_detail_platform_overlay_available',
        return_value=is_org_detail_platform_overlay_available_return_value,
    )
    mocker.patch(
        'lms.djangoapps.philu_overrides.context_processor.is_org_oef_prompt_available',
        return_value=is_org_oef_prompt_available_return_value,
    )
    mocker.patch(
        'lms.djangoapps.philu_overrides.context_processor.get_org_oef_update_prompt',
        return_value=get_org_oef_update_prompt_return_value
    )
    mocker.patch(
        'lms.djangoapps.philu_overrides.context_processor.is_org_detail_prompt_available',
        return_value=is_org_detail_prompt_available_return_value
    )
    mocker.patch(
        'lms.djangoapps.philu_overrides.context_processor.get_org_metric_update_prompt',
        return_value=get_org_metric_update_prompt_return_value
    )


@pytest.mark.parametrize(
    'is_active, is_ajax, user, path_to_append, expected_global_alert_message',
    [
        pytest.param(False, False, None, None, 'get_activation_alert_error_msg_dict', id='success'),
        pytest.param(False, True, None, None, [], id='ajax_failure'),
        pytest.param(False, False, AnonymousUserFactory.create(), None, [], id='auth_failure'),
        pytest.param(True, False, None, None, [], id='active_user_failure'),
        pytest.param(False, False, None, '/activate/', [], id='activation_url_failure')
    ]
)
def test_get_activation_error_alert_message(
    is_active, is_ajax, user, path_to_append, expected_global_alert_message, request_obj, mocker
):
    """
    Test success and all failure scenarios of activation error alert message

    1. Test that get_global_alert_messages should successfully return activation error message as the context when:
        - request is not AJAX,
        - user is authenticated,
        - user is inactive,
        - user is not requesting for activation

    2. Test that get_global_alert_messages should NOT return activation error message as the context when:
        2.1. request is AJAX
        2.2. user is unauthenticated
        2.3. user is already active
        2.4. user is directed to the activation url, i.e. when request.path contains '/activate/'
    """
    _mock_get_global_alert_messages_dependencies(mocker)

    request_obj.user.is_active = is_active

    if is_ajax:
        request_obj.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

    if user:
        request_obj.user = user

    if path_to_append:
        request_obj.path += path_to_append

    if expected_global_alert_message:
        expected_global_alert_message = [get_activation_alert_error_msg_dict(request_obj.user.id)]

    actual_global_alert_message = get_global_alert_messages(request_obj).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@pytest.mark.parametrize(
    'is_org_oef_prompt_available,'
    'get_org_oef_update_prompt,'
    'path_to_append,'
    'expected_global_alert_message,'
    'expected_oef_prompt',
    [
        pytest.param(True, True, '/oef/dashboard', [ORG_OEF_UPDATE_ALERT_MSG_DICT], True, id='success'),
        pytest.param(True, False, '/oef/dashboard', [], None, id='oef_prompt_failure'),
        pytest.param(False, True, '/oef/dashboard', [], None, id='oef_available_failure'),
        pytest.param(True, True, None, [], None, id='url_failure'),
    ]
)
def test_get_org_oef_update_alert_message(
    is_org_oef_prompt_available,
    get_org_oef_update_prompt,
    path_to_append,
    expected_global_alert_message,
    expected_oef_prompt,
    request_obj,
    mocker,
):
    """
    Test success and all failure scenarios of ORG_OEF_UPDATE_ALERT message

    1. Test that get_global_alert_messages returns ORG_OEF_UPDATE_ALERT as the context successfully when:
        - oef_update_prompt = True,
        - org_oef_prompt_available = True
        - request.path contains '/oef/dashboard'

    2. Test that get_global_alert_messages should NOT return ORG_OEF_UPDATE_ALERT as the context when:
        2.1. oef_update_prompt = False
        2.2. org_oef_prompt_available = False
        2.3. '/oef/dashboard' is not part of the request url
    """
    _mock_get_global_alert_messages_dependencies(
        mocker,
        is_org_oef_prompt_available_return_value=is_org_oef_prompt_available,
        get_org_oef_update_prompt_return_value=get_org_oef_update_prompt
    )

    if path_to_append:
        request_obj.path += path_to_append

    actual_result = get_global_alert_messages(request_obj)
    actual_global_alert_message = actual_result.get('global_alert_messages')
    actual_oef_prompt = actual_result.get('oef_prompt')

    assert expected_global_alert_message == actual_global_alert_message
    assert expected_oef_prompt == actual_oef_prompt


@pytest.mark.parametrize(
    'is_org_detail_prompt_available, get_org_metric_update_prompt, path_to_append, expected_global_alert_message',
    [
        pytest.param(True, True, '/organization/details/', [ORG_DETAILS_UPDATE_ALERT_MSG_DICT], id='success'),
        pytest.param(True, False, '/organization/details/', [], id='metric_prompt_failure'),
        pytest.param(False, True, '/organization/details/', [], id='detail_prompt_failure'),
        pytest.param(True, True, None, [], id='url_failure')
    ]
)
def test_get_org_details_update_alert_message(
    is_org_detail_prompt_available,
    get_org_metric_update_prompt,
    path_to_append,
    expected_global_alert_message,
    request_obj,
    mocker,
):
    """
    Test success and all failure scenarios of ORG_DETAILS_UPDATE_ALERT message

    1. Test that get_global_alert_messages returns ORG_DETAILS_UPDATE_ALERT as the context successfully when:
        - metric_update_prompt = True,
        - org_detail_prompt_available = True
        - request.path contains '/organization/details/'

    2. Test that get_global_alert_messages should NOT return ORG_DETAILS_UPDATE_ALERT as the context when:
        2.1. metric_update_prompt = False
        2.2. org_detail_prompt_available = False
        2.3. '/organization/details/' is not part of the request url
    """
    _mock_get_global_alert_messages_dependencies(
        mocker,
        is_org_detail_prompt_available_return_value=is_org_detail_prompt_available,
        get_org_metric_update_prompt_return_value=get_org_metric_update_prompt
    )

    if path_to_append:
        request_obj.path += path_to_append

    actual_global_alert_message = get_global_alert_messages(request_obj).get('global_alert_messages')

    assert expected_global_alert_message == actual_global_alert_message


@pytest.mark.parametrize(
    'is_org_detail_platform_overlay_available,'
    'is_org_detail_prompt_available,'
    'get_org_metric_update_prompt,'
    'path_to_append,'
    'expected_overlay_message',
    [
        pytest.param(True, True, True, None, True, id='success'),
        pytest.param(True, True, False, None, None, id='metric_prompt_failure'),
        pytest.param(True, False, True, None, None, id='detail_prompt_failure'),
        pytest.param(False, True, True, None, None, id='platform_overlay_failure'),
        pytest.param(True, True, True, '/oef/dashboard', None, id='oef_url_failure'),
        pytest.param(True, True, True, '/organization/details/', None, id='org_url_failure')
    ]
)
def test_overlay_message(
    is_org_detail_platform_overlay_available,
    is_org_detail_prompt_available,
    get_org_metric_update_prompt,
    path_to_append,
    expected_overlay_message,
    request_obj,
    mocker
):
    """
    Test success and all failure scenarios of overlay_message flag

    1. Test that get_global_alert_messages returns overlay_message = True when:
        - metric_update_prompt = True,
        - org_detail_prompt_available = True,
        - org_detail_platform_overlay_available = True,
        - request.path does not contain '/oef/dashboard'
        - request.path does not contain '/organization/details/'

    2. Test that get_global_alert_messages returns overlay_message = None when:
        2.1. metric_update_prompt = False
        2.2. org_detail_prompt_available = False
        2.3. org_detail_platform_overlay_available = False
        2.4. request.path contains '/oef/dashboard'
        2.5. request.path contains '/organization/details/'
    """
    _mock_get_global_alert_messages_dependencies(
        mocker,
        is_org_detail_platform_overlay_available_return_value=is_org_detail_platform_overlay_available,
        is_org_detail_prompt_available_return_value=is_org_detail_prompt_available,
        get_org_metric_update_prompt_return_value=get_org_metric_update_prompt
    )

    if path_to_append:
        request_obj.path += path_to_append

    actual_overlay_message = get_global_alert_messages(request_obj).get('overlay_message')

    assert expected_overlay_message == actual_overlay_message


def test_add_nodebb_endpoint():
    expected_result = NODEBB_END_POINT_DICT
    actual_result = add_nodebb_endpoint('request')
    assert expected_result == actual_result


def test_get_cdn_link():
    expected_result = CDN_LINK_DICT
    actual_result = get_cdn_link('request')
    assert expected_result == actual_result
