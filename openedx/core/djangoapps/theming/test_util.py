"""
Test helpers for Comprehensive Theming.
"""

from functools import wraps
import os
import os.path

from mock import patch

from django.conf import settings
from django.test.utils import override_settings

import edxmako

from .core import comprehensive_theme_changes


def with_comprehensive_theme(theme_dir):
    """
    A decorator to run a test with a particular comprehensive theme.

    Arguments:
        theme_dir (str): the full path to the theme directory to use.
            This will likely use `settings.REPO_ROOT` to get the full path.

    """
    # This decorator gets the settings changes needed for a theme, and applies
    # them using the override_settings and edxmako.paths.add_lookup context
    # managers.

    changes = comprehensive_theme_changes(theme_dir)

    def _decorator(func):                       # pylint: disable=missing-docstring
        @wraps(func)
        def _decorated(*args, **kwargs):        # pylint: disable=missing-docstring
            with override_settings(COMPREHENSIVE_THEME_DIR=theme_dir, **changes['settings']):
                with edxmako.save_lookups():
                    for template_dir in changes['mako_paths']:
                        edxmako.paths.add_lookup('main', template_dir, prepend=True)

                    return func(*args, **kwargs)
        return _decorated
    return _decorator


def with_is_edx_domain(is_edx_domain):
    """
    A decorator to run a test as if IS_EDX_DOMAIN is true or false.

    We are transitioning away from IS_EDX_DOMAIN and are moving toward an edX
    theme. This decorator changes both settings to let tests stay isolated
    from the details.

    Arguments:
        is_edx_domain (bool): are we an edX domain or not?

    """
    # This is weird, it's a decorator that conditionally applies other
    # decorators, which is confusing.
    def _decorator(func):                       # pylint: disable=missing-docstring
        if is_edx_domain:
            # This applies @with_comprehensive_theme to the func.
            func = with_comprehensive_theme(settings.REPO_ROOT / "themes" / "edx.org")(func)

        # This applies @patch.dict() to the func to set IS_EDX_DOMAIN.
        func = patch.dict('django.conf.settings.FEATURES', {"IS_EDX_DOMAIN": is_edx_domain})(func)

        return func

    return _decorator


def dump_theming_info():
    """Dump a bunch of theming information, for debugging."""
    for namespace, lookup in edxmako.LOOKUP.items():
        print "--- %s: %s" % (namespace, lookup.template_args['module_directory'])
        for directory in lookup.directories:
            print "  %s" % (directory,)

    print "=" * 80
    for dirname, __, filenames in os.walk(settings.MAKO_MODULE_DIR):
        print "%s ----------------" % (dir,)
        for filename in sorted(filenames):
            if filename.endswith(".pyc"):
                continue
            with open(os.path.join(dirname, filename)) as f:
                content = len(f.read())
            print "    %s: %d" % (filename, content)
