from .common import INSTALLED_APPS, MIDDLEWARE_CLASSES, FEATURES


def tuple_without(source_tuple, exclusion_list):
    """Return new tuple excluding any entries in the exclusion list. Needed because tuples
    are immutable. Order preserved."""
    return tuple([i for i in source_tuple if i not in exclusion_list])

INSTALLED_APPS = tuple_without(INSTALLED_APPS, ['debug_toolbar', 'debug_toolbar_mongo'])
INSTALLED_APPS += ('django_extensions',)
MIDDLEWARE_CLASSES = tuple_without(MIDDLEWARE_CLASSES, [
    'django_comment_client.utils.QueryCountDebugMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
])

DEBUG_TOOLBAR_MONGO_STACKTRACES = False

OAUTH_ENFORCE_SECURE = ""

import contracts
contracts.disable_all()
