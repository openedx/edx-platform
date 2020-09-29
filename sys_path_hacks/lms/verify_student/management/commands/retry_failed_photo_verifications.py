from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.management.commands.retry_failed_photo_verifications')

from lms.djangoapps.verify_student.management.commands.retry_failed_photo_verifications import *
