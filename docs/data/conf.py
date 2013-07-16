# -*- coding: utf-8 -*-
#

import sys, os

from docs.shared.conf import *


# Add any paths that contain templates here, relative to this directory.
templates_path.append('source/_templates')

sys.path.insert(0, os.path.abspath('.'))

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path.append('source/_static')


