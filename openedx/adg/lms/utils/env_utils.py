"""
All utility methods related to env variables
"""

import os


def is_testing_environment():
    """
    Check if our environment is testing or not.
    """
    return os.environ['DJANGO_SETTINGS_MODULE'] in ['lms.envs.test', 'cms.envs.test']
