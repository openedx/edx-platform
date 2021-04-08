"""
Toggles for bulk_email app
"""

from edx_toggles.toggles import SettingToggle


# .. toggle_name: bulk_email.EMAIL_USE_DEFAULT_FROM_FOR_BULK
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: If True, use the same DEFAULT_FROM_EMAIL as the from_addr for all bulk email, to avoid issues with spam filtering
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-10-01
# .. toggle_tickets: OSPR-4957


def is_email_use_default_from_bulk_enabled():
    return SettingToggle("EMAIL_USE_DEFAULT_FROM_FOR_BULK", default=False).is_enabled()
