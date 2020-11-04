from import_shims.warn import warn_deprecated_import

warn_deprecated_import('static_replace.management.commands', 'common.djangoapps.static_replace.management.commands')

from common.djangoapps.static_replace.management.commands import *
