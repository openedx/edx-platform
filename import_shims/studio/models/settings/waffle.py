from import_shims.warn import warn_deprecated_import

warn_deprecated_import('models.settings.waffle', 'cms.djangoapps.models.settings.waffle')

from cms.djangoapps.models.settings.waffle import *
