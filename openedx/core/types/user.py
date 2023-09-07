"""
Typing utilities for the User models.
"""
from typing import Union

import django.contrib.auth.models

User = Union[django.contrib.auth.models.User, django.contrib.auth.models.AnonymousUser]
