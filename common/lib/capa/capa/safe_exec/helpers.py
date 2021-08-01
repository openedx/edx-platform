"""
Helper methods related to safe exec.
"""

import requests
import json
import logging

from codejail.safe_exec import SafeExecException
from django.conf import settings
from django.utils.translation import ugettext as _
from edx_toggles.toggles import SettingDictToggle
from requests.exceptions import RequestException, HTTPError
from simplejson import JSONDecodeError

from .exceptions import CodejailServiceParseError, CodejailServiceStatusError, CodejailServiceUnavailable

log = logging.getLogger(__name__)

# .. toggle_name: ENABLE_CODEJAIL_REST_SERVICE
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Set this to True if you want to run Codejail code using
#   a separate VM or container and communicate with edx-platform using REST API.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2021-08-19
# .. toggle_target_removal_date: None
# .. toggle_warnings:
# .. toggle_tickets:
ENABLE_CODEJAIL_REST_SERVICE = SettingDictToggle(
    "FEATURES", "ENABLE_CODEJAIL_REST_SERVICE", default=False, module_name=__name__
)


def is_codejail_rest_service_enabled():
    return ENABLE_CODEJAIL_REST_SERVICE.is_enabled()


def get_codejail_rest_service_endpoint():
    return "".join([
        settings.CODE_JAIL_REST_SERVICE_HOST,
        "/api/v0/code-exec"])


def send_safe_exec_request(data, extra_files):
    """
    Sends a request to a codejail api service forwarding required code and files.
    Arguments:
        data: Dict containing code and othe parameters
            required for jailed code execution.
        extra_files: python_lib.zip file containing extra files
            required by the codejail execution.
    Returns:
        Response received from codejsail api service
    """
    globals_dict = data["globals_dict"]

    codejail_service_endpoint = get_codejail_rest_service_endpoint()
    payload = json.dumps(data)

    try:
        response = requests.post(
            codejail_service_endpoint,
            files=extra_files,
            data={'payload': payload},
            timeout=(settings.CODE_JAIL_REST_SERVICE_CONNECT_TIMEOUT, settings.CODE_JAIL_REST_SERVICE_READ_TIMEOUT)
        )

    except RequestException:
        log.error("Failed to connect to codejail api service: url=%s, params=%s",
                  codejail_service_endpoint, str(payload))
        raise CodejailServiceUnavailable(_("Codejail API Service is unavailable. Please try again in a few minutes."))  # lint-amnesty, pylint: disable=raise-missing-from

    try:
        response.raise_for_status()
    except HTTPError:
        raise CodejailServiceStatusError(_("Codejail API Service invalid response."))  # lint-amnesty, pylint: disable=raise-missing-from

    try:
        response_json = response.json()
    except JSONDecodeError:
        log.error("Invalid JSON response received from codejail api service: Response_Content=%s", response.content)
        raise CodejailServiceParseError(_("Invalid JSON response received from codejail api service."))  # lint-amnesty, pylint: disable=raise-missing-from

    emsg = response_json.get("emsg")
    exception = None

    if emsg:
        exception_msg = ". ".join([
            emsg,
            "For more information check Codejail Service logs."])

        exception = SafeExecException(exception_msg)

    globals_dict.update(response_json.get("globals_dict"))

    return emsg, exception
