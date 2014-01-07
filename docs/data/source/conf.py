# -*- coding: utf-8 -*-
#

import sys, os

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

sys.path.append(os.path.abspath('../../../'))
sys.path.append(os.path.abspath('../../'))

from docs.shared.conf import *

sys.path.insert(0, os.path.abspath('.'))

master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path.append('source/_templates')

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path.append('source/_static')

project = u'edX Data Documentation'
copyright = u'2013, edX Documentation Team'

# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''

#Added to turn off smart quotes so users can copy JSON values without problems.
html_use_smartypants = False