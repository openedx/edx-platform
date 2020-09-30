from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.event_transaction_utils')

from common.djangoapps.track.event_transaction_utils import *
