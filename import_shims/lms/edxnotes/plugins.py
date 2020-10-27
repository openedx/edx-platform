from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.plugins', 'lms.djangoapps.edxnotes.plugins')

from lms.djangoapps.edxnotes.plugins import *
