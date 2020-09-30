from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.anonymized_id_mapping')

from common.djangoapps.student.management.commands.anonymized_id_mapping import *
