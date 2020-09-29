from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.management.commands.create_orders_for_old_enterprise_course_enrollment')

from lms.djangoapps.commerce.management.commands.create_orders_for_old_enterprise_course_enrollment import *
