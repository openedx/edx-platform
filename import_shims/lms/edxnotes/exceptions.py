from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.exceptions', 'lms.djangoapps.edxnotes.exceptions')

from lms.djangoapps.edxnotes.exceptions import *
