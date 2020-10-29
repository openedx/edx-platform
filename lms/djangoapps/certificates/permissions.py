"""
Permission definitions for the certificates djangoapp
"""

from bridgekeeper import perms
from lms.djangoapps.courseware.rules import HasAccessRule

PREVIEW_CERTIFICATES = 'certificates.preview_certificates'
perms[PREVIEW_CERTIFICATES] = HasAccessRule('staff')
