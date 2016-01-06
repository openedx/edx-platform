import requests
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

log = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "authorization": 'Token {}'.format(settings.LABSTER_API_AUTH_TOKEN),
    "content-type": 'application/json',
    "accept": 'application/json',
}


class LabsterApiError(Exception):
    """
    This exception is raised in the case where problems with Labster API appear.
    """
    pass


def _send_request(url, method=None, data=None, params=None, headers=None):
    """
    Sends a request Labster API.
    """
    method = 'GET' if method is None else 'POST'

    _headers = DEFAULT_HEADERS.copy()

    if _headers and headers:
        _headers.update(headers)

    try:
        if method == 'POST':
            response = requests.post(url, headers=_headers, data=data, params=params)
        else:
            response = requests.get(url, headers=_headers, params=params)

        response.raise_for_status()
        return response.content

    except (requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL, requests.exceptions.MissingSchema) as ex:
        log.exception("Setup Labster endpoints in settings: \n%r", ex)
        raise ImproperlyConfigured(_("Setup Labster endpoints in settings"))

    except requests.RequestException as ex:
        log.exception("Labster API is unavailable:\n%r", ex)
        raise LabsterApiError(_("Labster API is unavailable."))

    except ValueError as ex:
        log.error("Invalid JSON:\n%r", ex)
