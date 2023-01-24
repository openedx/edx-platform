"""API utils"""

import logging
import requests

from django.conf import settings

log = logging.getLogger(__name__)


def get_personalized_course_recommendations(user_id):
    """Get personalize recommendations from Amplitude."""
    headers = {
        "Authorization": f"Api-Key {settings.AMPLITUDE_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "user_id": user_id,
        "get_recs": True,
        "rec_id": settings.REC_ID,
    }
    response = requests.get(settings.AMPLITUDE_URL, params=params, headers=headers)
    if response.status_code == 200:
        response = response.json()
        recommendations = response.get("userData", {}).get("recommendations", [])
        if recommendations:
            is_control = recommendations[0].get("is_control")
            has_is_control = recommendations[0].get("has_is_control")
            recommended_course_keys = recommendations[0].get("items")
            return is_control, has_is_control, recommended_course_keys

    return True, False, []
