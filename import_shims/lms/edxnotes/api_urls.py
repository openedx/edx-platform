from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.api_urls', 'lms.djangoapps.edxnotes.api_urls')

from lms.djangoapps.edxnotes.api_urls import *
