"""
A abstract class defining the interface methods that a notification will
implement

A NotificationRenderer knows how to take a NotificationMessage and present
a rendering of that message to a particular format, such as json, HTML, etc.

Note that a NotificationRender can be associated with more than one
NotificationType
"""

import abc

from importlib import import_module

_RENDERERS = {}


def register_renderer(class_name):
    """
    Adds a Renderer class - which must derive from BaseNotificationRenderer -
    to our in-proc cache. An instance will be created and a dictionary of
    class_name, instance will be built up
    """

    if class_name in _RENDERERS:
        return _RENDERERS[class_name]

    module_path, _, name = class_name.rpartition('.')
    class_ = getattr(import_module(module_path), name)

    renderer_instance = class_()
    _RENDERERS[class_name] = renderer_instance

    return renderer_instance


def get_all_renderers():
    """
    Returns the dictionary of registered renderers
    """
    return _RENDERERS


def clear_renderers():
    """
    Empties the dictionary of Renderer instances
    """
    _RENDERERS.clear()


def get_renderer_for_type(msg_type):
    """
    Returns the Renderer instance for the msg_type, None is not found
    """
    return _RENDERERS.get(msg_type.renderer)


class BaseNotificationRenderer(object):
    """
    Abstract Base Class for NotificationRender types.

    A NotificationRender knows how to convert a NotificationMessage payload into
    a human (e.g. HTML, text, etc) or machine (e.g. JSON) renderer format.

    Note: with the utilization of the abc.abstractmethod decorators you cannot
    create an instance of the class directly

    NOTE: Renderers will be singletons, so please do not store state inside of your
    Renderers
    """

    # don't allow instantiation of this class, it must be subclassed
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def can_render_format(self, render_format):
        """
        Returns (True/False) whether this renderer is able to convert the passed in message
        into the requested format.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def render(self, msg, render_format, lang):
        """
        Renders a subject line for this particular notification in the requested format and
        language

        If subclasses returns None or empty string, then the caller will
        subsitute a generic subject, e.g. "You have received a notification..."
        if the NotificationChannel *must* have a subject line, for example
        email-based delivery channels.

        If the requested language is not supported then subclasses should
        throw a NotificationLanguageNotSupported exception. The calling code
        should trap that and try with a different language
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_template_path(self, render_format):
        """
        Returns the raw template used. Note that msg payloads might be versioned
        so the renderer should do appropriate versioning of the templates
        """
        raise NotImplementedError()
