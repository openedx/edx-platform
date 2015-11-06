"""
Monkey patch implementation for a python_social_auth Django ORM method that is not Django 1.8-compatible.
Remove once the module fully supports Django 1.8!
"""

from django.db import transaction
from social.storage.django_orm import DjangoUserMixin
from social.apps.django_app.default.models import (
    UserSocialAuth, Nonce, Association, Code
)


def patch():
    """
    Monkey-patch the DjangoUserMixin class.
    """
    def create_social_auth_wrapper(wrapped_func):
        # pylint: disable=missing-docstring
        wrapped_func = wrapped_func.__func__

        def _create_social_auth(*args, **kwargs):
            # The entire reason for this monkey-patch is to wrap the create_social_auth call
            # in an atomic transaction. The call can sometime raise an IntegrityError, which is
            # caught and dealt with by python_social_auth - but not inside of an atomic transaction.
            # In Django 1.8, unless the exception is raised in an atomic transaction, the transaction
            # becomes unusable after the IntegrityError exception is raised.
            with transaction.atomic():
                return wrapped_func(*args, **kwargs)
        return classmethod(_create_social_auth)

    DjangoUserMixin.create_social_auth = create_social_auth_wrapper(DjangoUserMixin.create_social_auth)

    # Monkey-patch some social auth models' Meta class to squelch Django19 warnings.
    # pylint: disable=protected-access
    UserSocialAuth._meta.app_label = "default"
    Nonce._meta.app_label = "default"
    Association._meta.app_label = "default"
    Code._meta.app_label = "default"
