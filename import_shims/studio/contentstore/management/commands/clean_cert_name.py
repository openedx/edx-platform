from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.clean_cert_name')

from cms.djangoapps.contentstore.management.commands.clean_cert_name import *
