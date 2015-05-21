from django.conf import settings as base_settings

from microsite_configuration import microsite
from .templatetags.microsite import page_title_breadcrumbs


class MicrositeAwareSettings():
    """
    This class is a handy utility to make a call to the settings
    completely microsite aware by replacing the:
    from django.conf import settings
    with:
    from microsite_configuration import settings
    """

    def __getattr__(self, name):
        return microsite.get_value(name, base_settings.__getattr__(name))

settings = MicrositeAwareSettings()
