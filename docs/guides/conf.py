"""
Configuration for the developer documentation guides.
"""

import sys
from subprocess import check_call

import django
import six
from path import Path

root = Path("../..").abspath()
sys.path.insert(0, root)

# pylint: disable=wrong-import-position,redefined-builtin,wildcard-import
from docs.baseconf import *

# Hack the PYTHONPATH to match what LMS and Studio use so all the code
# can be successfully imported
sys.path.append(root / "docs/guides")
sys.path.append(root / "cms/djangoapps")
sys.path.append(root / "common/djangoapps")
sys.path.append(root / "common/lib/capa")
sys.path.append(root / "common/lib/safe_lxml")
sys.path.append(root / "common/lib/symmath")
sys.path.append(root / "common/lib/xmodule")
sys.path.append(root / "lms/djangoapps")
sys.path.append(root / "lms/envs")
sys.path.append(root / "openedx/core/djangoapps")
sys.path.append(root / "openedx/features")

# Use a settings module that allows all LMS and Studio code to be imported
# without errors.  If running sphinx-apidoc, we already set a different
# settings module to use in the on_init() hook of the parent process
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'docs.docs_settings'

django.setup()

project = u'edx-platform'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.ifconfig',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
]

# Mock out these external modules during code import to avoid errors
autodoc_mock_imports = [
    'MySQLdb',
    'contracts',
    'django_mysql',
    'pymongo',
]

# Start building a map of the directories relative to the repository root to
# run sphinx-apidoc against and the directories under "docs" in which to store
# the generated *.rst files
modules = {
    'cms': 'cms',
    'common/lib/capa/capa': 'common/lib/capa',
    'common/lib/safe_lxml/safe_lxml': 'common/lib/safe_lxml',
    'common/lib/symmath/symmath': 'common/lib/symmath',
    'common/lib/xmodule/xmodule': 'common/lib/xmodule',
    'lms': 'lms',
    'openedx': 'openedx',
}

# These Django apps under cms don't import correctly with the "cms.djangapps" prefix
# Others don't import correctly without it...INSTALLED_APPS entries are inconsistent
cms_djangoapps = ['contentstore', 'course_creators', 'xblock_config']
for app in cms_djangoapps:
    path = os.path.join('cms', 'djangoapps', app)
    modules[path] = path

# The Django apps under common must be imported directly, not under their path
for app in os.listdir(six.text_type(root / 'common' / 'djangoapps')):
    path = os.path.join('common', 'djangoapps', app)
    if os.path.isdir(six.text_type(root / path)) and app != 'terrain':
        modules[path] = path

# These Django apps under lms don't import correctly with the "lms.djangapps" prefix
# Others don't import correctly without it...INSTALLED_APPS entries are inconsistent
lms_djangoapps = ['badges', 'branding', 'bulk_email', 'courseware',
                  'coursewarehistoryextended', 'email_marketing', 'experiments', 'lti_provider',
                  'mobile_api', 'rss_proxy', 'shoppingcart', 'survey']
for app in lms_djangoapps:
    path = os.path.join('lms', 'djangoapps', app)
    modules[path] = path


def update_settings_module(service='lms'):
    """
    Set the "DJANGO_SETTINGS_MODULE" environment variable appropriately
    for the module sphinx-apidoc is about to be run on.
    """
    if os.environ['EDX_PLATFORM_SETTINGS'] == 'devstack_docker':
        settings_module = '{}.envs.devstack_docker'.format(service)
    else:
        settings_module = '{}.envs.devstack'.format(service)
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module


def on_init(app):  # pylint: disable=unused-argument
    """
    Run sphinx-apidoc after Sphinx initialization.

    Read the Docs won't run tox or custom shell commands, so we need this to
    avoid checking in the generated reStructuredText files.
    """
    docs_path = root / 'docs' / 'guides'
    apidoc_path = 'sphinx-apidoc'
    if hasattr(sys, 'real_prefix'):  # Check to see if we are in a virtualenv
        # If we are, assemble the path manually
        bin_path = os.path.abspath(os.path.join(sys.prefix, 'bin'))
        apidoc_path = os.path.join(bin_path, apidoc_path)
    exclude_dirs = ['envs', 'migrations', 'test', 'tests']
    exclude_dirs.extend(cms_djangoapps)
    exclude_dirs.extend(lms_djangoapps)
    exclude_files = ['admin.py', 'test.py', 'testing.py', 'tests.py', 'testutils.py', 'wsgi.py']
    for module in modules:
        module_path = six.text_type(root / module)
        output_path = six.text_type(docs_path / modules[module])
        args = [apidoc_path, '--ext-intersphinx', '-o',
                output_path, module_path]
        exclude = []
        if module == 'cms':
            update_settings_module('cms')
        else:
            update_settings_module('lms')
        for dirpath, dirnames, filenames in os.walk(module_path):
            to_remove = []
            for name in dirnames:
                if name in exclude_dirs:
                    to_remove.append(name)
                    exclude.append(os.path.join(dirpath, name))
            if 'features' in dirnames and 'openedx' not in dirpath:
                to_remove.append('features')
                exclude.append(os.path.join(dirpath, 'features'))
            for name in to_remove:
                dirnames.remove(name)
            for name in filenames:
                if name in exclude_files:
                    exclude.append(os.path.join(dirpath, name))
        if exclude:
            args.extend(exclude)
        check_call(args)


def setup(app):
    """Sphinx extension: run sphinx-apidoc."""
    event = b'builder-inited' if six.PY2 else 'builder-inited'
    app.connect(event, on_init)
