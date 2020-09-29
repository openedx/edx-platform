from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.urls')

from lms.djangoapps.edxnotes.urls import *
