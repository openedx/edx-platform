# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
# pylint: disable=protected-access
# pylint: disable=unused-argument

import os
from path import Path as path
import sys
import mock

MOCK_MODULES = [
    'ipware',
    'ip',
    'ipware.ip',
    'get_ip',
    'pygeoip',
    'ipaddr',
    'django_countries',
    'fields',
    'django_countries.fields',
    'opaque_keys',
    'opaque_keys.edx',
    'opaque_keys.edx.keys',
    'CourseKey',
    'UsageKey',
    'BlockTypeKey',
    'opaque_keys.edx.locations',
    'SlashSeparatedCourseKey',
    'Location',
    'opaque_keys.edx.locator',
    'Locator',
]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

sys.path.append('../../../../')

from docs.shared.conf import *


# Add any paths that contain templates here, relative to this directory.
#templates_path.append('source/_templates')


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path.append('source/_static')

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
root = path('../../../../').abspath()
sys.path.insert(0, root)
sys.path.append(root / "common/djangoapps")
sys.path.append('.')

#sys.path.insert(
#    0,
#    os.path.abspath(
#        os.path.normpath(
#            os.path.dirname(__file__) + '/../../../..'
#        )
#   )
#)


#  django configuration  - careful here
if on_rtd:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lms'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lms'

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx',
    'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.pngmath',
    'sphinx.ext.mathjax', 'sphinx.ext.viewcode', 'sphinxcontrib.napoleon']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['build', 'links.rst']


project = u'edX Enrollment API Version 1'
copyright = u'2015, edX'
