"""
Test helpers for Comprehensive Theming.
"""

from functools import wraps
import os
import os.path
import contextlib

from mock import patch

from django.conf import settings
from django.template import Engine
from django.test.utils import override_settings

import edxmako

from .core import comprehensive_theme_changes

EDX_THEME_DIR = settings.REPO_ROOT / "themes" / "edx.org"


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
                default_engine = Engine.get_default()
                dirs = default_engine.dirs[:]
                with edxmako.save_lookups():
                    for template_dir in changes['template_paths']:
                        edxmako.paths.add_lookup('main', template_dir, prepend=True)
                        dirs.insert(0, template_dir)
                    with patch.object(default_engine, 'dirs', dirs):
                        return func(*args, **kwargs)
        return _decorated
    return _decorator


def with_is_edx_domain(is_edx_domain):
    """
    A decorator to run a test as if request originated from edX domain or not.

    Arguments:
        is_edx_domain (bool): are we an edX domain or not?

    """
    # This is weird, it's a decorator that conditionally applies other
    # decorators, which is confusing.
    def _decorator(func):                       # pylint: disable=missing-docstring
        if is_edx_domain:
            # This applies @with_comprehensive_theme to the func.
            func = with_comprehensive_theme(EDX_THEME_DIR)(func)

        return func

    return _decorator


@contextlib.contextmanager
def with_edx_domain_context(is_edx_domain):
    """
    A function to run a test as if request originated from edX domain or not.

    Arguments:
        is_edx_domain (bool): are we an edX domain or not?

    """
    if is_edx_domain:
        changes = comprehensive_theme_changes(EDX_THEME_DIR)
        with override_settings(COMPREHENSIVE_THEME_DIR=EDX_THEME_DIR, **changes['settings']):
            with edxmako.save_lookups():
                for template_dir in changes['template_paths']:
                    edxmako.paths.add_lookup('main', template_dir, prepend=True)

                yield
    else:
        yield


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
