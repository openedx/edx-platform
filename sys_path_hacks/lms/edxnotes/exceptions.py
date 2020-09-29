from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.exceptions')

from lms.djangoapps.edxnotes.exceptions import *
