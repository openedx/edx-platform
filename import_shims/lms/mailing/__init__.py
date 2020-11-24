from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mailing', 'lms.djangoapps.mailing')

from lms.djangoapps.mailing import *
