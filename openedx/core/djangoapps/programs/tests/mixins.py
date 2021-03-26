"""Mixins for use during testing."""


from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramsApiConfigMixin:
    """Utilities for working with Programs configuration during testing."""

    DEFAULTS = {
        'enabled': True,
        'marketing_path': 'foo',
    }

    def create_programs_config(self, **kwargs):
        """Creates a new ProgramsApiConfig with DEFAULTS, updated with any provided overrides."""
        fields = dict(self.DEFAULTS, **kwargs)
        ProgramsApiConfig(**fields).save()

        return ProgramsApiConfig.current()
