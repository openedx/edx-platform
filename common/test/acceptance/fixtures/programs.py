"""
Tools to create programs-related data for use in bok choy tests.
"""


from common.test.acceptance.fixtures.config import ConfigModelFixture


class ProgramsConfigMixin(object):
    """Mixin providing a method used to configure the programs feature."""
    def set_programs_api_configuration(self, is_enabled=False):
        """Dynamically adjusts the Programs config model during tests."""
        ConfigModelFixture('/config/programs', {
            'enabled': is_enabled,
            'marketing_path': '/foo',
        }).install()
