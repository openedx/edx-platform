# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=W0622
# pylint: disable=W0212
# pylint: disable=W0613

import sys, os
from path import path

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'



sys.path.append('../../../../')

from docs.shared.conf import *


# Add any paths that contain templates here, relative to this directory.
templates_path.append('source/_templates')


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path.append('source/_static')

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
root = path('../../../..').abspath()
sys.path.insert(0, root)

sys.path.append(root / "common/djangoapps")
sys.path.append(root / "common/lib")
sys.path.append(root / "common/lib/capa")
sys.path.append(root / "common/lib/chem")
sys.path.append(root / "common/lib/sandbox-packages")
sys.path.append(root / "common/lib/xmodule")
sys.path.append(root / "common/lib/opaque_keys")
sys.path.append(root / "lms/djangoapps")
sys.path.append(root / "lms/djangoapps/api_manager")
sys.path.append(root / "lms/lib")
sys.path.append(root / "cms/djangoapps")
sys.path.append(root / "cms/lib")
sys.path.insert(0, os.path.abspath(os.path.normpath(os.path.dirname(__file__)
    + '/../../../')))
sys.path.append('.')

#  django configuration  - careful here
if on_rtd:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lms'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lms.envs.test'


# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx',
    'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.pngmath',
    'sphinx.ext.mathjax', 'sphinx.ext.viewcode', 'sphinxcontrib.napoleon']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['build']


# Output file base name for HTML help builder.
htmlhelp_basename = 'edXDocs'

project = u'edX Platform Developer Documentation'
copyright = u'2014, edX'

# --- Mock modules ------------------------------------------------------------

# Mock all the modules that the readthedocs build can't import

class Mock(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return Mock()

# The list of modules and submodules that we know give RTD trouble.
# Make sure you've tried including the relevant package in
# docs/share/requirements.txt before adding to this list.
MOCK_MODULES = [
    'bson',
    'bson.errors',
    'bson.objectid',
    'dateutil',
    'dateutil.parser',
    'fs',
    'fs.errors',
    'fs.osfs',
    'lazy',
    'mako',
    'mako.template',
    'matplotlib',
    'matplotlib.pyplot',
    'mock',
    'numpy',
    'oauthlib',
    'oauthlib.oauth1',
    'oauthlib.oauth1.rfc5849',
    'PIL',
    'pymongo',
    'pyparsing',
    'pysrt',
    'requests',
    'scipy.interpolate',
    'scipy.constants',
    'scipy.optimize',
    'yaml',
    'webob',
    'webob.multidict',
    ]

if on_rtd:
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = Mock()

# -----------------------------------------------------------------------------

# from http://djangosnippets.org/snippets/2533/
# autogenerate models definitions

import inspect
import types
from HTMLParser import HTMLParser


def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if not isinstance(s, basestring,):
        if hasattr(s, '__unicode__'):
            s = unicode(s)
        else:
            s = unicode(str(s), encoding, errors)
    elif not isinstance(s, unicode):
        s = unicode(s, encoding, errors)
    return s


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()




def process_docstring(app, what, name, obj, options, lines):
    """Autodoc django models"""

    # This causes import errors if left outside the function
    from django.db import models

    # If you want extract docs from django forms:
    # from django import forms
    # from django.forms.models import BaseInlineFormSet

    # Only look at objects that inherit from Django's base MODEL class
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        # Grab the field list from the meta class
        fields = obj._meta._fields()

        for field in fields:
            # Decode and strip any html out of the field's help text
            help_text = strip_tags(force_unicode(field.help_text))

            # Decode and capitalize the verbose name, for use if there isn't
            # any help text
            verbose_name = force_unicode(field.verbose_name).capitalize()

            if help_text:
                # Add the model field to the end of the docstring as a param
                # using the help text as the description
                lines.append(u':param %s: %s' % (field.attname, help_text))
            else:
                # Add the model field to the end of the docstring as a param
                # using the verbose name as the description
                lines.append(u':param %s: %s' % (field.attname, verbose_name))

            # Add the field's type to the docstring
            lines.append(u':type %s: %s' % (field.attname, type(field).__name__))
    return lines


def setup(app):
    """Setup docsting processors"""
    #Register the docstring processor with sphinx
    app.connect('autodoc-process-docstring', process_docstring)
