from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mailing.management', 'lms.djangoapps.mailing.management')

from lms.djangoapps.mailing.management import *
