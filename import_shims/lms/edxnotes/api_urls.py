from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'edxnotes.api_urls')

from lms.djangoapps.edxnotes.api_urls import *
