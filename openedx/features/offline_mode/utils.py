"""

"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()
log = logging.getLogger(__name__)


def get_offline_service_user():
    """
    Get the service user to render XBlock.
    """
    try:
        return User.objects.get(username=settings.OFFLINE_SERVICE_WORKER_USERNAME)
    except User.DoesNotExist as e:
        log.error(
            f'Service user with username {settings.OFFLINE_SERVICE_WORKER_USERNAME} to render XBlock does not exist.'
        )
        raise e
