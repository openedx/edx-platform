import logging
from django.conf import settings
from rest_framework import permissions


logger = logging.getLogger(__name__)


class SecretKeyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        request_secret_key = request.POST.get('secret_key', '')
        # TODO: put this into auth json file
        secret_key = settings.FEATURES.get('APPSEMBLER_SECRET_KEY', '')
        if not secret_key:
            logger.warning("APPSEMBLER_SECRET_KEY is not set")
            return False
        if request_secret_key != secret_key:
            logger.warning("Wrong secret key.")
            return False
        return True
