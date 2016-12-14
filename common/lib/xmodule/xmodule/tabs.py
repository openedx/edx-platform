"""
Implement CourseTab
"""
from abc import ABCMeta
import logging

from xblock.fields import List
from openedx.core.lib.api.plugins import PluginError

from django.core.files.storage import get_storage_class

log = logging.getLogger("edx.courseware")

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class CourseTab(object):
    """
    The Course Tab class is a data abstraction for all tabs (i.e., course navigation links) within a course.
    It is an abstract class - to be inherited by various tab types.
    Derived classes are expected to override methods as needed.
    When a new tab class is created, it should define the type and add it in this class' factory method.
    """
    __metaclass__ = ABCMeta

    # Class property that specifies the type of the tab.  It is generally a constant value for a
    # subclass, shared by all instances of the subclass.
    type = ''

    # The title of the tab, which should be internationalized using
    # ugettext_noop since the user won't be available in this context.
    title = None

    # Class property that specifies whether the tab can be hidden for a particular course
    is_hideable = False

    # Class property that specifies whether the tab is hidden for a particular course
    is_hidden = False

    # The relative priority of this view that affects the ordering (lower numbers shown first)
    priority = None

    # Class property that specifies whether the tab can be moved within a course's list of tabs
    is_movable = True

    # Class property that specifies whether the tab is a collection of other tabs
    is_collection = False

    # True if this tab is dynamically added to the list of tabs
    is_dynamic = False

    # True if this tab is a default for the course (when enabled)
    is_default = True

    # True if this tab can be included more than once for a course.
    allow_multiple = False

    # If there is a single view associated with this tab, this is the name of it
    view_name = None

    # True if this tab should be displayed only for instructors
    course_staff_only = False

    def __init__(self, tab_dict):
        """
        Initializes class members with values passed in by subclasses.

        Args:
            tab_dict (dict) - a dictionary of parameters used to build the tab.
        """

        self.name = tab_dict.get('name', self.title)
        self.tab_id = tab_dict.get('tab_id', getattr(self, 'tab_id', self.type))
        self.course_staff_only = tab_dict.get('course_staff_only', False)
        self.is_hidden = tab_dict.get('is_hidden', False)

        self.tab_dict = tab_dict

    @property
    def link_func(self):
        return self.tab_dict.get('link_func', link_reverse_func(self.view_name))

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if this course tab is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): an optional user interacting with the course (defaults to None)
        """
        raise NotImplementedError()

    def get(self, key, default=None):
        """
        Akin to the get method on Python dictionary objects, gracefully returns the value associated with the
        given key, or the default if key does not exist.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        """
        This method allows callers to access CourseTab members with the d[key] syntax as is done with
        Python dictionary objects.
        """
        if key == 'name':
            return self.name
        elif key == 'type':
            return self.type
        elif key == 'tab_id':
            return self.tab_id
        elif key == 'is_hidden':
            return self.is_hidden
        elif key == 'course_staff_only':
            return self.course_staff_only
        else:
            raise KeyError('Key {0} not present in tab {1}'.format(key, self.to_json()))

    def __setitem__(self, key, value):
        """
        This method allows callers to change CourseTab members with the d[key]=value syntax as is done with
        Python dictionary objects.  For example: course_tab['name'] = new_name

        Note: the 'type' member can be 'get', but not 'set'.
        """
        if key == 'name':
            self.name = value
        elif key == 'tab_id':
            self.tab_id = value
        elif key == 'is_hidden':
            self.is_hidden = value
        elif key == 'course_staff_only':
            self.course_staff_only = value
        else:
            raise KeyError('Key {0} cannot be set in tab {1}'.format(key, self.to_json()))

    def __eq__(self, other):
        """
        Overrides the equal operator to check equality of member variables rather than the object's address.
        Also allows comparison with dict-type tabs (needed to support callers implemented before this class
        was implemented).
        """

        if isinstance(other, dict) and not self.validate(other, raise_error=False):
            # 'other' is a dict-type tab and did not validate
            return False

        # allow tabs without names; if a name is required, its presence was checked in the validator.
        name_is_eq = (other.get('name') is None or self.name == other['name'])

        # only compare the persisted/serialized members: 'type' and 'name'
        return self.type == other.get('type') and name_is_eq

    def __ne__(self, other):
        """
        Overrides the not equal operator as a partner to the equal operator.
        """
        return not self == other

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Validates the given dict-type tab object to ensure it contains the expected keys.
        This method should be overridden by subclasses that require certain keys to be persisted in the tab.
        """
        return key_checker(['type'])(tab_dict, raise_error)

    @classmethod
    def load(cls, type_name, **kwargs):
        """
        Constructs a tab of the given type_name.

        Args:
            type_name (str) - the type of tab that should be constructed
            **kwargs - any other keyword arguments needed for constructing this tab

        Returns:
            an instance of the CourseTab subclass that matches the type_name
        """
        json_dict = kwargs.copy()
        json_dict['type'] = type_name
        return cls.from_json(json_dict)

    def to_json(self):
        """
        Serializes the necessary members of the CourseTab object to a json-serializable representation.
        This method is overridden by subclasses that have more members to serialize.

        Returns:
            a dictionary with keys for the properties of the CourseTab object.
        """
        to_json_val = {'type': self.type, 'name': self.name, 'course_staff_only': self.course_staff_only}
        if self.is_hidden:
            to_json_val.update({'is_hidden': True})
        return to_json_val

    @staticmethod
    def from_json(tab_dict):
        """
        Deserializes a CourseTab from a json-like representation.

        The subclass that is instantiated is determined by the value of the 'type' key in the
        given dict-type tab. The given dict-type tab is validated before instantiating the CourseTab object.

        If the tab_type is not recognized, then an exception is logged and None is returned.
        The intention is that the user should still be able to use the course even if a
        particular tab is not found for some reason.

        Args:
            tab: a dictionary with keys for the properties of the tab.

        Raises:
            InvalidTabsException if the given tab doesn't have the right keys.
        """
        # TODO: don't import openedx capabilities from common
        from openedx.core.lib.course_tabs import CourseTabPluginManager
        tab_type_name = tab_dict.get('type')
        if tab_type_name is None:
            log.error('No type included in tab_dict: %r', tab_dict)
            return None
        try:
            tab_type = CourseTabPluginManager.get_plugin(tab_type_name)
        except PluginError:
            log.exception(
                "Unknown tab type %r Known types: %r.",
                tab_type_name,
                CourseTabPluginManager.get_tab_types()
            )
            return None

        tab_type.validate(tab_dict)
        return tab_type(tab_dict=tab_dict)


class ComponentTabMixin(object):
    """
    A mixin for tabs that meet the component API (and can be rendered via Fragments).
    """
    component_name = None

    @property
    def link_func(self):
        def link_func(course, reverse_func):
            """ Returns a url for a given course and reverse function. """
            return reverse_func("component_tab", args=[course.id.to_deprecated_string(), self.type])

        return link_func

    @property
    def url_slug(self):
        return "tab/" + self.type

    def render_fragment(self, request, course):
        component = get_storage_class(self.component_name)()
        fragment = component.render_component(request, course_id=course.id.to_deprecated_string())
        return fragment


class StaticTab(CourseTab):
    """
    A custom tab.
    """
    type = 'static_tab'
    is_default = False  # A static tab is never added to a course by default
    allow_multiple = True

    def __init__(self, tab_dict=None, name=None, url_slug=None):
        def link_func(course, reverse_func):
            """ Returns a url for a given course and reverse function. """
            return reverse_func(self.type, args=[course.id.to_deprecated_string(), self.url_slug])

        self.url_slug = tab_dict.get('url_slug') if tab_dict else url_slug

        if tab_dict is None:
            tab_dict = dict()

        if name is not None:
            tab_dict['name'] = name

        tab_dict['link_func'] = link_func
        tab_dict['tab_id'] = 'static_tab_{0}'.format(self.url_slug)

        super(StaticTab, self).__init__(tab_dict)

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Static tabs are viewable to everyone, even anonymous users.
        """
        return True

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Ensures that the specified tab_dict is valid.
        """
        return (super(StaticTab, cls).validate(tab_dict, raise_error)
                and key_checker(['name', 'url_slug'])(tab_dict, raise_error))

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


class CourseTabList(List):
    """
    An XBlock field class that encapsulates a collection of Tabs in a course.
    It is automatically created and can be retrieved through a CourseDescriptor object: course.tabs
    """

    # TODO: Ideally, we'd like for this list of tabs to be dynamically
    # generated by the tabs plugin code. For now, we're leaving it like this to
    # preserve backwards compatibility.
    @staticmethod
    def initialize_default(course):
        """
        An explicit initialize method is used to set the default values, rather than implementing an
        __init__ method.  This is because the default values are dependent on other information from
        within the course.
        """

        course.tabs.extend([
            CourseTab.load('course_info'),
            CourseTab.load('courseware')
        ])

        # Presence of syllabus tab is indicated by a course attribute
        if hasattr(course, 'syllabus_present') and course.syllabus_present:
            course.tabs.append(CourseTab.load('syllabus'))

        # If the course has a discussion link specified, use that even if we feature
        # flag discussions off. Disabling that is mostly a server safety feature
        # at this point, and we don't need to worry about external sites.
        if course.discussion_link:
            discussion_tab = CourseTab.load(
                'external_discussion', name=_('External Discussion'), link=course.discussion_link
            )
        else:
            discussion_tab = CourseTab.load('discussion')

        course.tabs.extend([
            CourseTab.load('textbooks'),
            discussion_tab,
            CourseTab.load('wiki'),
            CourseTab.load('progress'),
        ])

    @staticmethod
    def get_discussion(course):
        """
        Returns the discussion tab for the given course.  It can be either of type 'discussion'
        or 'external_discussion'.  The returned tab object is self-aware of the 'link' that it corresponds to.
        """

        # the discussion_link setting overrides everything else, even if there is a discussion tab in the course tabs
        if course.discussion_link:
            return CourseTab.load(
                'external_discussion', name=_('External Discussion'), link=course.discussion_link
            )

        # find one of the discussion tab types in the course tabs
        for tab in course.tabs:
            if tab.type == 'discussion' or tab.type == 'external_discussion':
                return tab
        return None

    @staticmethod
    def get_tab_by_slug(tab_list, url_slug):
        """
        Look for a tab with the specified 'url_slug'.  Returns the tab or None if not found.
        """
        return next((tab for tab in tab_list if tab.get('url_slug') == url_slug), None)

    @staticmethod
    def get_tab_by_type(tab_list, tab_type):
        """
        Look for a tab with the specified type.  Returns the first matching tab.
        """
        return next((tab for tab in tab_list if tab.type == tab_type), None)

    @staticmethod
    def get_tab_by_id(tab_list, tab_id):
        """
        Look for a tab with the specified tab_id.  Returns the first matching tab.
        """
        return next((tab for tab in tab_list if tab.tab_id == tab_id), None)

    @staticmethod
    def iterate_displayable(course, user=None, inline_collections=True):
        """
        Generator method for iterating through all tabs that can be displayed for the given course and
        the given user with the provided access settings.
        """
        for tab in course.tabs:
            if tab.is_enabled(course, user=user) and not (user and tab.is_hidden):
                if tab.is_collection:
                    # If rendering inline that add each item in the collection,
                    # else just show the tab itself as long as it is not empty.
                    if inline_collections:
                        for item in tab.items(course):
                            yield item
                    elif len(list(tab.items(course))) > 0:
                        yield tab
                else:
                    yield tab

    @classmethod
    def upgrade_tabs(cls, tabs):
        """
        Reverse and Rename Courseware to Course and Course Info to Home Tabs.
        """
        if tabs and len(tabs) > 1:
            if tabs[0].get('type') == 'courseware' and tabs[1].get('type') == 'course_info':
                tabs[0], tabs[1] = tabs[1], tabs[0]
                tabs[0]['name'] = _('Home')
                tabs[1]['name'] = _('Course')

        return tabs

    @classmethod
    def validate_tabs(cls, tabs):
        """
        Check that the tabs set for the specified course is valid.  If it
        isn't, raise InvalidTabsException with the complaint.

        Specific rules checked:
        - if no tabs specified, that's fine
        - if tabs specified, first two must have type 'courseware' and 'course_info', in that order.

        """
        if tabs is None or len(tabs) == 0:
            return

        if len(tabs) < 2:
            raise InvalidTabsException("Expected at least two tabs.  tabs: '{0}'".format(tabs))

        if tabs[0].get('type') != 'course_info':
            raise InvalidTabsException(
                "Expected first tab to have type 'course_info'.  tabs: '{0}'".format(tabs))

        if tabs[1].get('type') != 'courseware':
            raise InvalidTabsException(
                "Expected second tab to have type 'courseware'.  tabs: '{0}'".format(tabs))

        # the following tabs should appear only once
        # TODO: don't import openedx capabilities from common
        from openedx.core.lib.course_tabs import CourseTabPluginManager
        for tab_type in CourseTabPluginManager.get_tab_types():
            if not tab_type.allow_multiple:
                cls._validate_num_tabs_of_type(tabs, tab_type.type, 1)

    @staticmethod
    def _validate_num_tabs_of_type(tabs, tab_type, max_num):
        """
        Check that the number of times that the given 'tab_type' appears in 'tabs' is less than or equal to 'max_num'.
        """
        count = sum(1 for tab in tabs if tab.get('type') == tab_type)
        if count > max_num:
            msg = (
                "Tab of type '{type}' appears {count} time(s). "
                "Expected maximum of {max} time(s)."
            ).format(
                type=tab_type, count=count, max=max_num,
            )
            raise InvalidTabsException(msg)

    def to_json(self, values):
        """
        Overrides the to_json method to serialize all the CourseTab objects to a json-serializable representation.
        """
        json_data = []
        if values:
            for val in values:
                if isinstance(val, CourseTab):
                    json_data.append(val.to_json())
                elif isinstance(val, dict):
                    json_data.append(val)
                else:
                    continue
        return json_data

    def from_json(self, values):
        """
        Overrides the from_json method to de-serialize the CourseTab objects from a json-like representation.
        """
        self.upgrade_tabs(values)
        self.validate_tabs(values)
        tabs = []
        for tab_dict in values:
            tab = CourseTab.from_json(tab_dict)
            if tab:
                tabs.append(tab)
        return tabs


# Validators
#  A validator takes a dict and raises InvalidTabsException if required fields are missing or otherwise wrong.
# (e.g. "is there a 'name' field?).  Validators can assume that the type field is valid.
def key_checker(expected_keys):
    """
    Returns a function that checks that specified keys are present in a dict.
    """

    def check(actual_dict, raise_error=True):
        """
        Function that checks whether all keys in the expected_keys object is in the given actual_dict object.
        """
        missing = set(expected_keys) - set(actual_dict.keys())
        if not missing:
            return True
        if raise_error:
            raise InvalidTabsException(
                "Expected keys '{0}' are not present in the given dict: {1}".format(expected_keys, actual_dict)
            )
        else:
            return False

    return check


def link_reverse_func(reverse_name):
    """
    Returns a function that takes in a course and reverse_url_func,
    and calls the reverse_url_func with the given reverse_name and course's ID.

    This is used to generate the url for a CourseTab without having access to Django's reverse function.
    """
    return lambda course, reverse_url_func: reverse_url_func(reverse_name, args=[course.id.to_deprecated_string()])


def need_name(dictionary, raise_error=True):
    """
    Returns whether the 'name' key exists in the given dictionary.
    """
    return key_checker(['name'])(dictionary, raise_error)


class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass


class UnequalTabsException(Exception):
    """
    A complaint about tab lists being unequal
    """
    pass
