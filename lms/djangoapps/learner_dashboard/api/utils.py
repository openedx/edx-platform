"""API utils"""

import logging
import requests
from django.conf import settings

log = logging.getLogger(__name__)


def get_personalized_course_recommendations(user_id):
    """ get personalize recommendations from Amplitude. """
    headers = {
        'Authorization': f'Api-Key {settings.AMPLITUDE_API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'user_id': user_id,
        'get_recs': True,
        'rec_id': settings.REC_ID,
    }
    try:
        response = requests.get(settings.AMPLITUDE_URL, params=params, headers=headers)
        if response.status_code == 200:
            response = response.json()
            is_control = response['userData']['recommendations'][0]['is_control']
            course_keys = response['userData']['recommendations'][0]['items']
            return is_control, course_keys
    except Exception as ex:  # pylint: disable=broad-except
        log.exception(f'Cannot get recommendations from Amplitude: {ex}')

    return True, []
