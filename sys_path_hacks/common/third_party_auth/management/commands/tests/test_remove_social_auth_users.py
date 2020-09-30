from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'third_party_auth.management.commands.tests.test_remove_social_auth_users')

from common.djangoapps.third_party_auth.management.commands.tests.test_remove_social_auth_users import *
