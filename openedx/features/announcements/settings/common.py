"""Common settings for Announcements"""


def plugin_settings(settings):
    """
    Common settings for Announcements
    .. toggle_name: FEATURES['ENABLE_ANNOUNCEMENTS']
    .. toggle_implementation: SettingDictToggle
    .. toggle_default: False
    .. toggle_description: This feature can be enabled to show system wide announcements
       on the sidebar of the learner dashboard. Announcements can be created by Global Staff
       users on maintenance dashboard of studio. Maintenance dashboard can accessed at
       https://{studio.domain}/maintenance
    .. toggle_warning: TinyMCE is needed to show an editor in the studio.
    .. toggle_use_cases: open_edx
    .. toggle_creation_date: 2017-11-08
    .. toggle_tickets: https://github.com/openedx/edx-platform/pull/16496
    """
    settings.FEATURES['ENABLE_ANNOUNCEMENTS'] = False
    # Configure number of announcements to show per page
    settings.FEATURES['ANNOUNCEMENTS_PER_PAGE'] = 5
