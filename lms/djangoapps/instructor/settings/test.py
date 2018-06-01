"""Test suite environment variables unique to the instructor plugin."""


def plugin_settings(settings):
    """Settings for the instructor plugin."""
    # Enable this feature for course staff grade downloads, to enable acceptance tests
    settings.FEATURES['ENABLE_GRADE_DOWNLOADS'] = True
    settings.FEATURES['ALLOW_COURSE_STAFF_GRADE_DOWNLOADS'] = True
