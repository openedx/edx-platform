from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxnotes.tests', 'lms.djangoapps.edxnotes.tests')

from lms.djangoapps.edxnotes.tests import *
