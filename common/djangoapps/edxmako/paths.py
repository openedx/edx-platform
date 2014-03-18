"""
Set up lookup paths for mako templates.
"""
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
    def add_directory(self, directory):
        """
        Add a new directory to the template lookup path.
        """
        self.directories.append(os.path.normpath(directory))


def clear_lookups(namespace):
    """
    Remove mako template lookups for the given namespace.
    """
    if namespace in LOOKUP:
        del LOOKUP[namespace]

def add_lookup(namespace, directory, package=None):
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
    templates.add_directory(directory)


def lookup_template(namespace, name):
    """
    Look up a Mako template by namespace and name.
    """
    return LOOKUP[namespace].get_template(name)
