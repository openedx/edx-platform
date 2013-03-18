import pkg_resources
import logging

log = logging.getLogger(__name__)

class PluginNotFoundError(Exception):
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
                raise PluginNotFoundError(identifier)

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
