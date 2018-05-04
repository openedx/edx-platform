"""
Configuration defaults for the heartbeat djangoapp

Configures what checks to run by default in normal and "extended"/heavy mode,
as well as providing settings for the default checks themselves
"""

HEARTBEAT_DEFAULT_CHECKS = [
    '.default_checks.check_modulestore',
    '.default_checks.check_database',
]

HEARTBEAT_EXTENDED_DEFAULT_CHECKS = (
    '.default_checks.check_celery',
)

HEARTBEAT_CELERY_TIMEOUT = 5
