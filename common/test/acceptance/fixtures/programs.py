"""
Tools to create programs-related data for use in bok choy tests.
"""
from common.test.acceptance.fixtures.config import ConfigModelFixture


class ProgramsConfigMixin(object):
    """Mixin providing a method used to configure the programs feature."""
    def set_programs_api_configuration(self, is_enabled=False, api_version=1):
        """Dynamically adjusts the Programs config model during tests."""
        ConfigModelFixture('/config/programs', {
            'enabled': is_enabled,
            'api_version_number': api_version,
            'cache_ttl': 0,
            'marketing_path': '/foo',
            'enable_student_dashboard': is_enabled,
            'enable_certification': is_enabled,
            'program_listing_enabled': is_enabled,
            'program_details_enabled': is_enabled,
        }).install()
