"""Common settings unique to the remote gradebook plugin."""


def plugin_settings(settings):
    """Settings for the remote gradebook plugin."""
    settings.REMOTE_GRADEBOOK = {}
    settings.REMOTE_GRADEBOOK_USER = None
    settings.REMOTE_GRADEBOOK_PASSWORD = None
    settings.FEATURES['ENABLE_INSTRUCTOR_REMOTE_GRADEBOOK_CONTROLS'] = False
