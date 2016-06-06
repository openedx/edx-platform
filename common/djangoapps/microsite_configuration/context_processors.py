""" Django template ontext processors. """

from django.conf import settings

from microsite_configuration import microsite


def microsite_context(request):  # pylint: disable=unused-argument
    return {
        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME)
    }
