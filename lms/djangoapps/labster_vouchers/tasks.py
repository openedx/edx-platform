"""
Labster Voucher tasks.
"""
import logging

import requests
from requests.exceptions import RequestException
from cms import CELERY_APP
from django.conf import settings


log = logging.getLogger(__name__)


@CELERY_APP.task
def activate_voucher(voucher, user_id, email, context_id):
    """
    Task that activates the voucher.
    """
    url = settings.LABSTER_ENDPOINTS.get('voucher_activate')
    headers = {
        "authorization": 'Token {}'.format(settings.LABSTER_API_AUTH_TOKEN),
    }

    data = {
        'user_id': user_id,
        'email': email,
        'context_id': context_id,
        'voucher': voucher,
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
    except RequestException as ex:
        msg = (
            "Issues with voucher activation: user_id='%s', email='%s', "
            "context_id='%s', voucher='%s',\nerror:\n%r"
        )
        log.exception(msg, user_id, email, context_id, voucher, ex)
        return "error"
    return "succeeded"
