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
                return self.merge_dict(name)
            return microsite.get_value(name, base_settings.__getattr__(name))
        except KeyError:
            base_settings.__getattr__(name)

    def merge_dict(self, name):
        """
        Handles the merge of two dictonaries, the one from the base_settings
        updated to include the overrides defined at the microsite
        """
        if microsite.has_override_value(name):
            temp = base_settings.__getattr__(name).copy()
            temp.update(microsite.get_value(name, {}))
            return temp
        else:
            return base_settings.__getattr__(name)


settings = MicrositeAwareSettings()
