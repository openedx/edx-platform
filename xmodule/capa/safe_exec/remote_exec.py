"""
Helper methods related to safe exec.
"""

import json
import logging
from importlib import import_module
import requests

from codejail.safe_exec import SafeExecException
from django.conf import settings
from edx_toggles.toggles import SettingToggle
from requests.exceptions import RequestException, HTTPError
from simplejson import JSONDecodeError

from django.utils.translation import gettext as _
from .exceptions import CodejailServiceParseError, CodejailServiceStatusError, CodejailServiceUnavailable

log = logging.getLogger(__name__)

# .. toggle_name: ENABLE_CODEJAIL_REST_SERVICE
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: Set this to True if you want to run Codejail code using
#   a separate VM or container and communicate with edx-platform using REST API.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2021-08-19
ENABLE_CODEJAIL_REST_SERVICE = SettingToggle(
    "ENABLE_CODEJAIL_REST_SERVICE", default=False, module_name=__name__
)


def is_codejail_rest_service_enabled():
    return ENABLE_CODEJAIL_REST_SERVICE.is_enabled()


def get_remote_exec(*args, **kwargs):
    """Get remote exec function based on setting and executes it."""
    remote_exec_function_name = settings.CODE_JAIL_REST_SERVICE_REMOTE_EXEC
    try:
        mod_name, func_name = remote_exec_function_name.rsplit('.', 1)
        remote_exec_module = import_module(mod_name)
        remote_exec_function = getattr(remote_exec_module, func_name)
        if not remote_exec_function:
            remote_exec_function = send_safe_exec_request_v0
    except ModuleNotFoundError:
        return send_safe_exec_request_v0(*args, **kwargs)
    return remote_exec_function(*args, **kwargs)


def get_codejail_rest_service_endpoint():
    return f"{settings.CODE_JAIL_REST_SERVICE_HOST}/api/v0/code-exec"


def send_safe_exec_request_v0(data):
    """
    Sends a request to a codejail api service forwarding required code and files.
    Arguments:
        data: Dict containing code and other parameters
            required for jailed code execution.
            It also includes extra_files (python_lib.zip) required by the codejail execution.
    Returns:
        Response received from codejail api service
    """
    globals_dict = data["globals_dict"]
    extra_files = data.pop("extra_files")

    codejail_service_endpoint = get_codejail_rest_service_endpoint()
    payload = json.dumps(data)

    try:
        response = requests.post(
            codejail_service_endpoint,
            files=extra_files,
            data={'payload': payload},
            timeout=(settings.CODE_JAIL_REST_SERVICE_CONNECT_TIMEOUT, settings.CODE_JAIL_REST_SERVICE_READ_TIMEOUT)
        )

    except RequestException as err:
        log.error("Failed to connect to codejail api service: url=%s, params=%s",
                  codejail_service_endpoint, str(payload))
        raise CodejailServiceUnavailable(_(
            "Codejail API Service is unavailable. "
            "Please try again in a few minutes."
        )) from err

    try:
        response.raise_for_status()
    except HTTPError as err:
        raise CodejailServiceStatusError(_("Codejail API Service invalid response.")) from err

    try:
        response_json = response.json()
    except JSONDecodeError as err:
        log.error("Invalid JSON response received from codejail api service: Response_Content=%s", response.content)
        raise CodejailServiceParseError(_("Invalid JSON response received from codejail api service.")) from err

    emsg = response_json.get("emsg")
    exception = None

    if emsg:
        exception_msg = f"{emsg}. For more information check Codejail Service logs."
        exception = SafeExecException(exception_msg)

    globals_dict.update(response_json.get("globals_dict"))

    return emsg, exception
