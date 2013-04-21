'''
Utilities for contentstore tests
'''

import json

from student.models import Registration
from django.contrib.auth.models import User


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)


def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)
