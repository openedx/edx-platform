"""Mixins for use during testing."""
from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramsApiConfigMixin(object):
    """Utilities for working with Programs configuration during testing."""

    DEFAULTS = {
        'enabled': True,
        'api_version_number': 1,
        'internal_service_url': 'http://internal.programs.org/',
        'public_service_url': 'http://public.programs.org/',
        'cache_ttl': 0,
        'enable_studio_tab': True,
        'enable_certification': True,
        'program_listing_enabled': True,
        'program_details_enabled': True,
        'marketing_path': 'foo',
    }

    def create_programs_config(self, **kwargs):
        """Creates a new ProgramsApiConfig with DEFAULTS, updated with any provided overrides."""
        fields = dict(self.DEFAULTS, **kwargs)
        ProgramsApiConfig(**fields).save()

        return ProgramsApiConfig.current()
