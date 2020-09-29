from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.plugins')

from lms.djangoapps.edxnotes.plugins import *
