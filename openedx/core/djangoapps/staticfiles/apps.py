"""
Configuration for static assets. Shared by LMS and CMS.
"""
from django.contrib.staticfiles.apps import StaticFilesConfig


class EdxPlatformStaticFilesConfig(StaticFilesConfig):
    """
    A thin wrapper around the standard django.contrib.staticfiles app
    which adds the proper file & folder ignore patterns for edx-platform
    static asset collection.

    This allows devs & operators to run:
        ./manage.py [lms|cms] collectstatic

    instead of:
        ./manage.py [lms|cms] collectstatic --ignore geoip --ignore sass ... etc.
    """

    ignore_patterns = StaticFilesConfig.ignore_patterns + [

        "geoip",  # Geo-IP data, only accessed in Python
        "sass",  # We compile these out, don't need the source files in staticfiles
        "xmodule_js",  # Symlink for tests.

        # Karma test related files:
        "fixtures",
        "karma_*.js",
        "spec",
        "spec_helpers",
        "spec-helpers",
    ]
