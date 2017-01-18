from django.conf import settings


def add_hook(method_location):
    settings.SOCIAL_AUTH_PIPELINE += (method_location, )
