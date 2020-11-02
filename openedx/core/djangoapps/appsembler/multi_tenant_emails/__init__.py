"""
This app enabled Multi-Tenant Emails on Tahoe via migrations and other helpers.

This app rolls back what the `common/djangoapps/database_fixups` does.
"""


from django.conf import settings

if settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS:
    def test_dummy():
        """Dummy test function so tox succeeds."""
        pass
