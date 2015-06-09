# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
# pylint: disable=protected-access
# pylint: disable=unused-argument

import os
from path import path
import sys
import mock

MOCK_MODULES = [
    'lxml',
    'requests',
    'xblock',
    'fields',
    'xblock.fields',
    'frament',
    'xblock.fragment',
    'webob',
    'multidict',
    'webob.multidict',
    'core',
    'xblock.core',
    'runtime',
    'xblock.runtime',
    'sortedcontainers',
    'contracts',
    'plugin',
    'xblock.plugin',
    'opaque_keys.edx.asides',
    'asides',
    'dogstats_wrapper',
    'fs',
    'fs.errors',
    'edxmako',
    'edxmako.shortcuts',
    'shortcuts',
    'crum',
    'opaque_keys.edx.locator',
    'LibraryLocator',
    'Location',
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
    'Locator',
    'south',
    'modelsinspector',
    'south.modelsinspector',
    'add_introspection_rules',
    'courseware',
    'access',
    'courseware.access',
    'is_mobile_available_for_user',
    'courseware.model_data',
    'courseware.module_render',
    'courseware.views',
    'util.request',
    'eventtracking',
    'xmodule',
    'xmodule.exceptions',
    'xmodule.modulestore',
    'xmodule.modulestore.exceptions',
    'xmodule.modulestore.django',
    'courseware.models',
    'milestones',
    'milestones.api',
    'milestones.models',
    'milestones.exceptions',
    'ratelimitbackend',
    'analytics',
    'courseware.courses',
    'staticfiles',
    'storage',
    'staticfiles.storage',
    'content',
    'xmodule.contentstore',
    'xmodule.contentstore.content',
    'xblock.exceptions',
    'xmodule.seq_module',
    'xmodule.vertical_module',
    'xmodule.x_module',
    'nltk',
    'ratelimitbackend',
    'ratelimitbackend.exceptions',
    'social',
    'social.apps',
    'social.apps.django_app',
    'social.backends',
    'mako',
    'exceptions',
    'mako.exceptions',
    'boto',
    'exception',
    'boto.exception',
    'PIL',
    'reportlab',
    'lib',
    'reportlab.lib',
    'pdfgen',
    'canvas',
    'pdfgen',
    'pdfgen.canvas',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.styles',
    'reportlab.platypus',
    'reportlab.platypus.tables',
    'boto',
    's3',
    'connection',
    'boto.s3',
    'boto.s3.connection',
    'boto.s3.key',
    'Crypto',
    'Crypto.Cipher',
    'Crypto.PublicKey',
    'openid',
    'store',
    'interface',
    'openid.store',
    'store.interface',
    'openid.store.interface',
    'external_auth.views',
    'html_to_text',
    'mail_utils',
    'ratelimitbackend.backends',
    'social.apps.django_app.default',
    'social.exceptions',
    'social.pipeline',
    'xmodule.error_module',
    'accounts.api',
    'modulestore.mongo.base',
    'xmodule.modulestore.mongo',
    'xmodule.modulestore.mongo.base',
    'edxval',
    'edxval.api',
    'model_utils',
    'model_utils.models',
    'model_utils.managers',
    'certificates',
    'certificates.models',
    'certificates.models.GeneratedCertificate',
    'shoppingcart',
    'shopppingcart.models',
    'shopppingcart.api',
    'api',
    'student',
    'student.views',
    'student.forms',
    'student.models',
    'celery',
    'celery.task',
    'student.roles',
    'embargo.models',
    'xmodule.vertical_block',
    'vertical_block',
    'errors',
    'UserNotFound',
    'UserNotAuthorized',
    'AccountUpdateError',
    'AccountValidationError',
    'transaction',
    'parsers',
    'MergePatchParser',
    'get_account_settings',
    'update_account_settings',
    'serializers',
    'profile_images.images',
    'xmodule.course_module'


]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock(class_that_is_extended=object)

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
root = path('../../../..').abspath()
sys.path.insert(0, root)
sys.path.append(root / "common/lib/xmodule")
sys.path.append(root / "common/djangoapps")
sys.path.append(root / "lms/djangoapps")
sys.path.append(root / "openedx/core/djangoapps")

sys.path.insert(
    0,
    os.path.abspath(
        os.path.normpath(
            os.path.dirname(__file__) + '/../../../'
        )
    )
)
sys.path.append('.')

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

project = u'EdX Platform APIs'
copyright = u'2015, edX'

exclude_patterns = ['build', 'links.rst']
