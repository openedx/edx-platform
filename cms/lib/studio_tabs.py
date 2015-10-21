"""Studio tab plugin manager and API."""
import abc

from openedx.core.lib.api.plugins import PluginManager


class StudioTabPluginManager(PluginManager):
    """Manager for all available Studio tabs.

    Examples of Studio tabs include Courses, Libraries, and Programs. All Studio
    tabs should implement `StudioTab`.
    """
    NAMESPACE = 'openedx.studio_tab'

    @classmethod
    def get_enabled_tabs(cls):
        """Returns a list of enabled Studio tabs."""
        tabs = cls.get_available_plugins()
        enabled_tabs = [tab for tab in tabs.viewvalues() if tab.is_enabled()]

        return enabled_tabs


class StudioTab(object):
    """Abstract class used to represent Studio tabs.

    Examples of Studio tabs include Courses, Libraries, and Programs.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def tab_text(self):
        """Text to display in a tab used to navigate to a list of instances of this tab.

        Should be internationalized using `ugettext_noop()` since the user won't be available in this context.
        """
        pass

    @abc.abstractproperty
    def button_text(self):
        """Text to display in a button used to create a new instance of this tab.

        Should be internationalized using `ugettext_noop()` since the user won't be available in this context.
        """
        pass

    @abc.abstractproperty
    def view_name(self):
        """Name of the view used to render this tab.

        Used within templates in conjuction with Django's `reverse()` to generate a URL for this tab.
        """
        pass

    @abc.abstractmethod
    def is_enabled(cls, user=None):  # pylint: disable=no-self-argument,unused-argument
        """Indicates whether this tab should be enabled.

        This is a class method; override with @classmethod.

        Keyword Arguments:
            user (User): The user signed in to Studio.
        """
        pass
