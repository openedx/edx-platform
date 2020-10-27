from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views.api_urls', 'lms.djangoapps.instructor.views.api_urls')

from lms.djangoapps.instructor.views.api_urls import *
