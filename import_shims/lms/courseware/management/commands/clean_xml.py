from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management.commands.clean_xml', 'lms.djangoapps.courseware.management.commands.clean_xml')

from lms.djangoapps.courseware.management.commands.clean_xml import *
