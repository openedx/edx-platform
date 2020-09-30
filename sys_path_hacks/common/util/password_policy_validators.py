from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.password_policy_validators')

from common.djangoapps.util.password_policy_validators import *
