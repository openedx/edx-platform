from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.serializers', 'lms.djangoapps.experiments.serializers')

from lms.djangoapps.experiments.serializers import *
