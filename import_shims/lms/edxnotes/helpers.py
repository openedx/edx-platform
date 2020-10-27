from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.helpers')

from lms.djangoapps.edxnotes.helpers import *
