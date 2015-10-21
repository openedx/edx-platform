"""
Monkey patch implementation for a python_social_auth Django ORM method that is not Django 1.8-compatible.
Remove once the module fully supports Django 1.8!
"""

from django.db import transaction
from social.storage.django_orm import DjangoUserMixin


def patch():
    """
    Monkey-patch the DjangoUserMixin class.
    """
    def create_social_auth_wrapper(wrapped_func):
        wrapped_func = wrapped_func.__func__
        def _w(*args, **kwargs):
            with transaction.atomic():
                return wrapped_func(*args, **kwargs)
        return classmethod(_w)

    DjangoUserMixin.create_social_auth = create_social_auth_wrapper(DjangoUserMixin.create_social_auth)
