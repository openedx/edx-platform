"""
This is the root package for all core Open edX functionality. In particular,
the djangoapps subpackage is the location for all Django apps that are shared
between LMS and CMS.

This file adds a definition for the Microsite Settings with a nicer notation
"""
from microsite_configuration import MicrositeAwareSettings


settings = MicrositeAwareSettings()  # pylint: disable=invalid-name
