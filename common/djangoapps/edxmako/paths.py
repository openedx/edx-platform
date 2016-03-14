"""
Set up lookup paths for mako templates.
"""

import hashlib
import contextlib
import os
import pkg_resources

from django.conf import settings
from mako.lookup import TemplateLookup

from . import LOOKUP


class DynamicTemplateLookup(TemplateLookup):
    """
    A specialization of the standard mako `TemplateLookup` class which allows
    for adding directories progressively.
    """
    def __init__(self, *args, **kwargs):
        super(DynamicTemplateLookup, self).__init__(*args, **kwargs)
        self.__original_module_directory = self.template_args['module_directory']

    def __repr__(self):
        return "<{0.__class__.__name__} {0.directories}>".format(self)

    def add_directory(self, directory, prepend=False):
        """
        Add a new directory to the template lookup path.
        """
        if prepend:
            self.directories.insert(0, os.path.normpath(directory))
        else:
            self.directories.append(os.path.normpath(directory))

        # Since the lookup path has changed, the compiled modules might be
        # wrong because now "foo.html" might be a completely different template,
        # and "foo.html.py" in the module directory has no way to know that.
        # Update the module_directory argument to point to a directory
        # specifically for this lookup path.
        unique = hashlib.md5(":".join(str(d) for d in self.directories)).hexdigest()
        self.template_args['module_directory'] = os.path.join(self.__original_module_directory, unique)

        # Also clear the internal caches. Ick.
        self._collection.clear()
        self._uri_cache.clear()


def clear_lookups(namespace):
    """
    Remove mako template lookups for the given namespace.
    """
    if namespace in LOOKUP:
        del LOOKUP[namespace]


def add_lookup(namespace, directory, package=None, prepend=False):
    """
    Adds a new mako template lookup directory to the given namespace.

    If `package` is specified, `pkg_resources` is used to look up the directory
    inside the given package.  Otherwise `directory` is assumed to be a path
    in the filesystem.
    """
    templates = LOOKUP.get(namespace)
    if not templates:
        LOOKUP[namespace] = templates = DynamicTemplateLookup(
            module_directory=settings.MAKO_MODULE_DIR,
            output_encoding='utf-8',
            input_encoding='utf-8',
            default_filters=['decode.utf8'],
            encoding_errors='replace',
        )
    if package:
        directory = pkg_resources.resource_filename(package, directory)
    templates.add_directory(directory, prepend=prepend)


def lookup_template(namespace, name):
    """
    Look up a Mako template by namespace and name.
    """
    return LOOKUP[namespace].get_template(name)


@contextlib.contextmanager
def save_lookups():
    """
    A context manager to save and restore the Mako template lookup path.

    Useful for testing.

    """
    # Make a copy of the list of directories for each namespace.
    namespace_dirs = {namespace: list(look.directories) for namespace, look in LOOKUP.items()}

    try:
        yield
    finally:
        # Get rid of all the lookups.
        LOOKUP.clear()

        # Re-create the lookups from our saved list.
        for namespace, directories in namespace_dirs.items():
            for directory in directories:
                add_lookup(namespace, directory)
