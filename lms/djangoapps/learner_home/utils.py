"""API utils"""

import logging
import requests
from time import time

from django.conf import settings

log = logging.getLogger(__name__)
LH_DEBUG = True


def exec_time_logged(func):
    """Wrap the function and return result and execution time"""

    # IF debugging is on, log function run lengths
    if LH_DEBUG:

        def wrap_func(*args, **kwargs):
            # Time the function operation
            t1 = time()
            result = func(*args, **kwargs)
            t2 = time()

            # Display lists / sets as their lengths instead of actual items
            debug_args = []
            for arg in args:
                if isinstance(arg, list) or isinstance(arg, set):
                    debug_args.append(f"<list: (len {len(arg)})>")
                else:
                    debug_args.append(arg)

            # Log the output
            log.info(f"{func.__name__!r} args:{debug_args} completed in {(t2-t1):.4f}s")

            return result

        return wrap_func

    # If debugging is off, don't do any logging
    else:
        return func


def get_personalized_course_recommendations(user_id):
    """ Get personalize recommendations from Amplitude. """
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
            recommendations = response.get('userData', {}).get('recommendations', [])
            if recommendations:
                is_control = recommendations[0].get('is_control')
                recommended_course_keys = recommendations[0].get('items')
                return is_control, recommended_course_keys
    except Exception as ex:  # pylint: disable=broad-except
        log.warning(f'Cannot get recommendations from Amplitude: {ex}')

    return True, []
