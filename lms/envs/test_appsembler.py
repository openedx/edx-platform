from .test import *

COMPREHENSIVE_THEME_DIRS = [
    REPO_ROOT / "themes",
    REPO_ROOT / "common/test",
    REPO_ROOT / "common/test/appsembler",
]
DEFAULT_SITE_THEME = "appsembler-theme"
USE_S3_FOR_CUSTOMER_THEMES = False

import logging
logging.disable(logging.WARNING)
