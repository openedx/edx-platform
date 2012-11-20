import logging
import pkg_resources
import yaml
import os
import inspect

from functools import partial
from lxml import etree
from pprint import pprint
from collections import namedtuple
from pkg_resources import resource_listdir, resource_string, resource_isdir

from .modulestore import Location
from .timeparse import parse_time

from .contentstore.content import StaticContent, XASSET_SRCREF_PREFIX

log = logging.getLogger('mitx.' + __name__)


def dummy_track(event_type, event):
    pass


class ModuleMissingError(Exception):
    pass

class MissingXModuleView(Exception):
    pass


class Plugin(object):
    """
    Base class for a system that uses entry_points to load plugins.

    Implementing classes are expected to have the following attributes:

        entry_point: The name of the entry point to load plugins from
    """

    _plugin_cache = None

    @classmethod
    def load_class(cls, identifier, default=None):
        """
        Loads a single class instance specified by identifier. If identifier
        specifies more than a single class, then logs a warning and returns the
        first class identified.

        If default is not None, will return default if no entry_point matching
        identifier is found. Otherwise, will raise a ModuleMissingError
        """
        if cls._plugin_cache is None:
            cls._plugin_cache = {}

        if identifier not in cls._plugin_cache:
            identifier = identifier.lower()
            classes = list(pkg_resources.iter_entry_points(
                    cls.entry_point, name=identifier))

            if len(classes) > 1:
                log.warning("Found multiple classes for {entry_point} with "
                            "identifier {id}: {classes}. "
                            "Returning the first one.".format(
                    entry_point=cls.entry_point,
                    id=identifier,
                    classes=", ".join(
                            class_.module_name for class_ in classes)))

            if len(classes) == 0:
                if default is not None:
                    return default
                raise ModuleMissingError(identifier)

            cls._plugin_cache[identifier] = classes[0].load()
        return cls._plugin_cache[identifier]

    @classmethod
    def load_classes(cls):
        """
        Returns a list of containing the identifiers and their corresponding classes for all
        of the available instances of this plugin
        """
        return [(class_.name, class_.load())
                for class_
                in pkg_resources.iter_entry_points(cls.entry_point)]


def register_view(view_name):
    def wrapper(fn):
        fn.view_name = view_name
        return fn
    return wrapper

class XModule(Plugin):
    ''' Implements a generic learning module.

        Subclasses must at a minimum provide a definition for get_html in order
        to be displayed to users.

        See the HTML module for a simple example.
    '''

    entry_point = "xmodule.v2"

    def __init__(self, runtime, content, course_settings, user_preferences, student_state, *args, **kwargs):
        '''
        Construct a new xmodule

        runtime: A ModuleSystem allowing access to external resources

        content: A dictionary containing the data that the content author
            created to define this module instance

        course_settings: A dictionary containing the data that describes how the module
            should operate

        user_preferences: A dictionary containing the data that describes the
            global preferences for this user about this module type

        student_state: A dictionary containing the data that a student has
            entered for this module

        kwargs: Optional arguments. Subclasses should always accept kwargs and
            pass them to the parent class constructor.
        '''
        self.runtime = runtime
        self.content = content
        self.course_settings = course_settings
        self.user_preferences = user_preferences
        self.student_state = student_state

        self._view_name = None

    @staticmethod
    def render(module, view_name, context):
        """
        Render the specified view from the supplied module

        module: The XModule to render

        view_name: The string name of the view to render

        context: Data parent XModules make available to their children
        during rendering.

        """
        # Make children use the appropriate render context
        try:
            module._view_name = view_name
            return module.find_view(view_name)(context)
        finally:
            module._view_name = None

    def render_child(self, child, view_name=None, context=None):
        """
        Render a view on a child module. If view_name isn't supplied,
        render the same view on the child that is currently being rendered on the parent
        """
        if view_name is None:
            view_name = self._view_name

        return XModule.render(child, view_name, context or {})

    def find_view(self, view_name):
        for method_name, method_fn in inspect.getmembers(self, inspect.ismethod):
            if getattr(method_fn, 'view_name', None) == view_name:
                return method_fn
        raise MissingXModuleView(self.__class__, view_name)

    @property
    def children(self):
        return self.runtime.children

Template = namedtuple("Template", "metadata data children")

class XModuleDescriptor():
    pass
