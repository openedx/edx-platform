"""Common settings unique to the remote gradebook plugin."""


def plugin_settings(settings):
    """Settings for the remote gradebook plugin."""
    settings.CANVAS_ACCESS_TOKEN = "7867~Yk4SaesY21OB4yJ7hbQhTCFewl3xpJrhGg6rBcnSNopcVzyyeapIA61qUV65qxwR"
    settings.CANVAS_BASE_URL = "https://mit.test.instructure.com"
    settings.FEATURES['ENABLE_CANVAS_INTEGRATION'] = True
