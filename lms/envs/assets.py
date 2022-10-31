from path import Path as path

from openedx.core.lib.derived import derive_settings

from .common import *

STATIC_ROOT_BASE = os.environ.get('STATIC_ROOT_BASE', STATIC_ROOT_BASE)
WEBPACK_CONFIG_PATH = os.environ.get('WEBPACK_CONFIG_PATH', WEBPACK_CONFIG_PATH)

if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)

derive_settings(__name__)


