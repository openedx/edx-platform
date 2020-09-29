from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.tests')

from lms.djangoapps.edxnotes.tests import *
