"""
This file implements a class which is a handy utility to make any
call to the settings completely microsite aware by replacing the:

from django.conf import settings

with:

from microsite_configuration import settings
or
from openedx.conf import settings

"""
from django.conf import settings as base_settings

from microsite_configuration import microsite
from .templatetags.microsite import page_title_breadcrumbs


class MicrositeAwareSettings(object):
    """
    This class is a proxy object of the settings object from django.
    It will try to get a value from the microsite and default to the
    django settings
    """

    def __getattr__(self, name):
        try:
            if isinstance(microsite.get_value(name), dict):
                return microsite.get_dict(name, base_settings.__getattr__(name))
            return microsite.get_value(name, base_settings.__getattr__(name))
        except KeyError:
            base_settings.__getattr__(name)


settings = MicrositeAwareSettings()  # pylint: disable=invalid-name
