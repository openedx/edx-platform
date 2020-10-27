from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.urls', 'lms.djangoapps.edxnotes.urls')

from lms.djangoapps.edxnotes.urls import *
