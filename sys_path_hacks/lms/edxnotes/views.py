from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.views')

from lms.djangoapps.edxnotes.views import *
