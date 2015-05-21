"""
Microsite backend that reads the configuration from a file

"""

from microsite_configuration.backends.base import (
    BaseMicrositeBackend,
    BaseMicrositeTemplateBackend,
)


class FilebasedMicrositeBackend(BaseMicrositeBackend):
    """
    Microsite backend that reads the microsites definitions
    from a dictionary called MICROSITE_CONFIGURATION in the settings file.
    """

    def __init__(self, **kwargs):
        super(FilebasedMicrositeBackend, self).__init__(**kwargs)


class FilebasedMicrositeTemplateBackend(BaseMicrositeTemplateBackend):
    """
    Microsite backend that loads templates from filesystem.
    """
    pass
