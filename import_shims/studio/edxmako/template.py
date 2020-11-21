from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxmako.template', 'common.djangoapps.edxmako.template')

from common.djangoapps.edxmako.template import *
