"""
edX Platform support for credentials.

This package will be used as a wrapper for interacting with the credentials
service.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='credentials')

# Waffle flag to enable the experimental Student Records feature
STUDENT_RECORDS_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'student_records')
