import string
import random
import uuid

from django.contrib.auth import authenticate, login, get_backends
from django.contrib.auth.models import User
from lti_provider.models import LtiUser


def create_lti_user(params):
    lti_user_id = params['user_id']
    edx_user_id = generate_random_edx_username()
    edx_password = uuid.uuid4()

    edx_user = User.objects.create_user(
        username=edx_user_id,
        password=edx_password,
        email='{}@lti.example.com'.format(edx_user_id)
    )
    edx_user.save()

    lti_user = LtiUser(
        lti_user_id=lti_user_id,
        edx_user_id=edx_user_id,
    )
    lti_user.save()
    return lti_user


def switch_user(request, lti_user):
    user = User.objects.get(username=lti_user.edx_user_id)
    user.backend = 'nobody'
    if user:
        login(request, user)


def generate_random_edx_username():
    allowable_chars = string.ascii_letters + string.digits
    username = ''
    for _i in range(30):
        username = username + random.SystemRandom().choice(allowable_chars)
    return username
