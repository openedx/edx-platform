"""
Adds support for first class features that can be added to the edX platform.
"""

from stevedore.extension import ExtensionManager

# Stevedore extension point namespaces
COURSE_VIEW_TYPE_NAMESPACE = 'openedx.course_view_type'


class PluginError(Exception):
    """
    Base Exception for when an error was found regarding features.
    """
    pass


class PluginManager(object):
    """
    Base class that manages plugins to the edX platform.
    """
    @classmethod
    def get_available_plugins(cls):
        """
        Returns a dict of all the plugins that have been made available through the platform.
        """
        # Note: we're creating the extension manager lazily to ensure that the Python path
        # has been correctly set up. Trying to create this statically will fail, unfortunately.
        if not hasattr(cls, "_plugins"):
            plugins = {}
            extension_manager = ExtensionManager(namespace=cls.NAMESPACE)  # pylint: disable=no-member
            for plugin_name in extension_manager.names():
                plugins[plugin_name] = extension_manager[plugin_name].plugin
            cls._plugins = plugins
        return cls._plugins

    @classmethod
    def get_plugin(cls, name):
        """
        Returns the plugin with the given name.
        """
        plugins = cls.get_available_plugins()
        if name not in plugins:
            raise PluginError("No such plugin {name} for entry point {namespace}".format(
                name=name,
                namespace=cls.NAMESPACE  # pylint: disable=no-member
            ))
        return plugins[name]


class CourseViewType(object):
    """
    Base class of all course view type plugins.
    """
    name = None
    title = None
    view_name = None
    is_persistent = False

    # The course field that indicates that this feature is enabled
    feature_flag_field_name = None

    @classmethod
    def is_enabled(cls, course, settings, user=None):  # pylint: disable=unused-argument
        """Returns true if this course view is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings
            user (User): the user interacting with the course
        """
        raise NotImplementedError()

    @classmethod
    def validate(cls, tab_dict, raise_error=True):  # pylint: disable=unused-argument
        """
        Validates the given dict-type `tab_dict` object to ensure it contains the expected keys.
        This method should be overridden by subclasses that require certain keys to be persisted in the tab.
        """
        return True


class CourseViewTypeManager(PluginManager):
    """
    Manager for all of the course view types that have been made available.

    All course view types should implement `CourseViewType`.
    """
    NAMESPACE = COURSE_VIEW_TYPE_NAMESPACE
