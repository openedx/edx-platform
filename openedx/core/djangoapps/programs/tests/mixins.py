"""
Broadly-useful mixins for use in automated tests.
"""

from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramsApiConfigMixin(object):
    """
    Programs api configuration utility methods for testing.
    """

    INTERNAL_URL = "http://internal/"
    PUBLIC_URL = "http://public/"

    DEFAULTS = dict(
        internal_service_url=INTERNAL_URL,
        public_service_url=PUBLIC_URL,
        api_version_number=1,
    )

    def create_config(self, **kwargs):
        """
        DRY helper.  Create a new ProgramsApiConfig with self.DEFAULTS, updated
        with any kwarg overrides.
        """
        ProgramsApiConfig(**dict(self.DEFAULTS, **kwargs)).save()
