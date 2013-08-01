# -*- coding: utf-8 -*-
#

import sys, os

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if on_rtd:   # Add to syspath so RTD will find the common conf file
    sys.path.append('../../../')

from docs.shared.conf import *


# Add any paths that contain templates here, relative to this directory.
templates_path.append('source/_templates')


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path.append('source/_static')


