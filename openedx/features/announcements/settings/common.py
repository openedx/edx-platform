"""Common settings for Announcements"""


def plugin_settings(settings):
    """
    Common settings for Announcements
    """
    settings.FEATURES['ENABLE_ANNOUNCEMENTS'] = False
    # Configure number of announcements to show per page
    settings.FEATURES['ANNOUNCEMENTS_PER_PAGE'] = 5
