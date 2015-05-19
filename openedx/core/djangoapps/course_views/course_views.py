"""
Tabs for courseware.
"""
from openedx.core.lib.api.plugins import PluginManager
from xmodule.tabs import CourseTab, link_reverse_func

_ = lambda text: text


# Stevedore extension point namespaces
COURSE_VIEW_TYPE_NAMESPACE = 'openedx.course_view_type'


class CourseViewType(object):
    """
    Base class of all course view type plugins.
    """
    name = None    # The name of the view type, which is used for persistence and view type lookup
    title = None    # The title of the view, which should be internationalized
    priority = None    # The relative priority of this view that affects the ordering (lower numbers shown first)
    view_name = None    # The name of the Django view to show this view
    tab_id = None    # The id to be used to show a tab for this view
    is_movable = True    # True if this course view can be moved
    is_dynamic = False    # True if this course view is dynamically added to the list of tabs
    is_default = True    # True if this course view is a default for the course (when enabled)
    is_hideable = False    # True if this course view's visibility can be toggled by the author

    @classmethod
    def is_enabled(cls, course, django_settings, user=None):  # pylint: disable=unused-argument
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

    @classmethod
    def create_tab(cls, tab_dict):
        """
        Returns the tab that will be shown to represent an instance of a view.
        """
        return CourseViewTab(cls, tab_dict=tab_dict)


class CourseViewTypeManager(PluginManager):
    """
    Manager for all of the course view types that have been made available.

    All course view types should implement `CourseViewType`.
    """
    NAMESPACE = COURSE_VIEW_TYPE_NAMESPACE

    @classmethod
    def get_course_view_types(cls):
        """
        Returns the list of available course view types in their canonical order.
        """
        def compare_course_view_types(first_type, second_type):
            """Compares two course view types, for use in sorting."""
            first_priority = first_type.priority
            second_priority = second_type.priority
            if not first_priority == second_priority:
                if not first_priority:
                    return 1
                elif not second_priority:
                    return -1
                else:
                    return first_priority - second_priority
            first_name = first_type.name
            second_name = second_type.name
            if first_name < second_name:
                return -1
            elif first_name == second_name:
                return 0
            else:
                return 1
        course_view_types = cls.get_available_plugins().values()
        course_view_types.sort(cmp=compare_course_view_types)
        return course_view_types


class CourseViewTab(CourseTab):
    """
    A tab that renders a course view.
    """

    def __init__(self, course_view_type, tab_dict=None):
        super(CourseViewTab, self).__init__(
            name=tab_dict.get('name', course_view_type.title) if tab_dict else course_view_type.title,
            tab_id=course_view_type.tab_id if course_view_type.tab_id else course_view_type.name,
            link_func=link_reverse_func(course_view_type.view_name),
        )
        self.type = course_view_type.name
        self.course_view_type = course_view_type
        self.is_hideable = course_view_type.is_hideable
        self.is_hidden = tab_dict.get('is_hidden', False) if tab_dict else False
        self.is_collection = course_view_type.is_collection if hasattr(course_view_type, 'is_collection') else False
        self.is_movable = course_view_type.is_movable

    def is_enabled(self, course, settings, user=None):
        if not super(CourseViewTab, self).is_enabled(course, settings, user=user):
            return False
        return self.course_view_type.is_enabled(course, settings, user=user)

    def __getitem__(self, key):
        if key == 'is_hidden':
            return self.is_hidden
        else:
            return super(CourseViewTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'is_hidden':
            self.is_hidden = value
        else:
            super(CourseViewTab, self).__setitem__(key, value)

    def to_json(self):
        to_json_val = super(CourseViewTab, self).to_json()
        if self.is_hidden:
            to_json_val.update({'is_hidden': True})
        return to_json_val

    def items(self, course):
        """ If this tab is a collection, this will fetch the items in the collection. """
        for item in self.course_view_type.items(course):
            yield item
