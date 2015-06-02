"""
Tabs for courseware.
"""
from openedx.core.lib.api.plugins import PluginManager
from xmodule.tabs import CourseTab

_ = lambda text: text


# Stevedore extension point namespaces
COURSE_VIEW_TYPE_NAMESPACE = 'openedx.course_view_type'


def link_reverse_func(reverse_name):
    """
    Returns a function that takes in a course and reverse_url_func,
    and calls the reverse_url_func with the given reverse_name and course' ID.
    """
    return lambda course, reverse_url_func: reverse_url_func(reverse_name, args=[course.id.to_deprecated_string()])


class CourseViewType(object):
    """
    Base class of all course view type plugins.

    These are responsible for defining tabs that can be displayed in the courseware. In order to create
    and register a new CourseViewType. Create a class (either in edx-platform or in a pip installable library)
    that inherits from CourseViewType and create a new entry in setup.py.

    For example:

        entry_points={
            "openedx.course_view_type": [
                "new_view = my_feature.NewCourseViewType",
            ],
        }

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
    allow_multiple = False  # True if this tab can be included more than once for a course.

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        """Returns true if this course view is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): an optional user interacting with the course (defaults to None)
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

    def is_enabled(self, course, user=None):
        """ Returns True if the tab has been enabled for this course and this user, False otherwise. """
        if not super(CourseViewTab, self).is_enabled(course, user=user):
            return False
        return self.course_view_type.is_enabled(course, user=user)

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
        """ Return a dictionary representation of this tab. """
        to_json_val = super(CourseViewTab, self).to_json()
        if self.is_hidden:
            to_json_val.update({'is_hidden': True})
        return to_json_val

    def items(self, course):
        """ If this tab is a collection, this will fetch the items in the collection. """
        for item in self.course_view_type.items(course):
            yield item


class StaticTab(CourseTab):
    """
    A custom tab.
    """
    type = 'static_tab'

    def __init__(self, tab_dict=None, name=None, url_slug=None):
        def link_func(course, reverse_func):
            """ Returns a url for a given course and reverse function. """
            return reverse_func(self.type, args=[course.id.to_deprecated_string(), self.url_slug])

        self.url_slug = tab_dict['url_slug'] if tab_dict else url_slug
        super(StaticTab, self).__init__(
            name=tab_dict['name'] if tab_dict else name,
            tab_id='static_tab_{0}'.format(self.url_slug),
            link_func=link_func,
        )

    def __getitem__(self, key):
        if key == 'url_slug':
            return self.url_slug
        else:
            return super(StaticTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'url_slug':
            self.url_slug = value
        else:
            super(StaticTab, self).__setitem__(key, value)

    def to_json(self):
        """ Return a dictionary representation of this tab. """
        to_json_val = super(StaticTab, self).to_json()
        to_json_val.update({'url_slug': self.url_slug})
        return to_json_val

    def __eq__(self, other):
        if not super(StaticTab, self).__eq__(other):
            return False
        return self.url_slug == other.get('url_slug')
