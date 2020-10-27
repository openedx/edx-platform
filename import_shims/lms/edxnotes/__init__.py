from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes', 'lms.djangoapps.edxnotes')

from lms.djangoapps.edxnotes import *
