from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.management.commands.tests.test_create_orders_for_old_enterprise_course_enrollmnet')

from lms.djangoapps.commerce.management.commands.tests.test_create_orders_for_old_enterprise_course_enrollmnet import *
