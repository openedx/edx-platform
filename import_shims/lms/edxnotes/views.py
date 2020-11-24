from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.views', 'lms.djangoapps.edxnotes.views')

from lms.djangoapps.edxnotes.views import *
