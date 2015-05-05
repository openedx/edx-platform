"""
Implement CourseTab
"""
from abc import ABCMeta, abstractmethod

from xblock.fields import List

# We should only scrape strings for i18n in this file, since the target language is known only when
# they are rendered in the template.  So ugettext gets called in the template.
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

    # Class property that specifies whether the tab can be hidden for a particular course
    is_hideable = False

    # Class property that specifies whether the tab can be moved within a course's list of tabs
    is_movable = True

    # Class property that specifies whether the tab is a collection of other tabs
    is_collection = False

    def __init__(self, name, tab_id, link_func):
        """
        Initializes class members with values passed in by subclasses.

        Args:
            name: The name of the tab

            tab_id: Intended to be a unique id for this tab, although it is currently not enforced
            within this module.  It is used by the UI to determine which page is active.

            link_func: A function that computes the link for the tab,
            given the course and a reverse-url function as input parameters
        """

        self.name = name

        self.tab_id = tab_id

        self.link_func = link_func

    def is_enabled(self, course, settings, user=None):  # pylint: disable=unused-argument
        """
        Determines whether the tab is enabled for the given course and a particular user.
        This method is to be overridden by subclasses when applicable.  The base class
        implementation always returns True.

        Args:
            course: An xModule CourseDescriptor

            settings: The configuration settings, including values for:
             WIKI_ENABLED
             FEATURES['ENABLE_DISCUSSION_SERVICE']
             FEATURES['ENABLE_EDXNOTES']
             FEATURES['ENABLE_STUDENT_NOTES']
             FEATURES['ENABLE_TEXTBOOK']

            user: An optional user for whom the tab will be displayed. If none,
                then the code should assume a staff user or an author.

        Returns:
            A boolean value to indicate whether this instance of the tab is enabled.
        """
        return True

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
        return not (self == other)

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Validates the given dict-type tab object to ensure it contains the expected keys.
        This method should be overridden by subclasses that require certain keys to be persisted in the tab.
        """
        return key_checker(['type'])(tab_dict, raise_error)

    def to_json(self):
        """
        Serializes the necessary members of the CourseTab object to a json-serializable representation.
        This method is overridden by subclasses that have more members to serialize.

        Returns:
            a dictionary with keys for the properties of the CourseTab object.
        """
        return {'type': self.type, 'name': self.name}

    @staticmethod
    def from_json(tab_dict):
        """
        Deserializes a CourseTab from a json-like representation.

        The subclass that is instantiated is determined by the value of the 'type' key in the
        given dict-type tab. The given dict-type tab is validated before instantiating the CourseTab object.

        Args:
            tab: a dictionary with keys for the properties of the tab.

        Raises:
            InvalidTabsException if the given tab doesn't have the right keys.
        """
        available_tab_types = CourseTabManager.get_tab_types()
        tab_type_name = tab_dict.get('type')
        if tab_type_name not in available_tab_types:
            raise InvalidTabsException(
                'Unknown tab type {0}. Known types: {1}'.format(tab_type_name, available_tab_types)
            )
        tab_type = available_tab_types[tab_dict['type']]
        tab_type.validate(tab_dict)
        # TODO: don't import openedx capabilities from common
        from openedx.core.lib.plugins.api import CourseViewType
        if issubclass(tab_type, CourseViewType):
            return CourseViewTab(tab_type, tab_dict=tab_dict)
        else:
            return tab_type(tab_dict=tab_dict)


class CourseTabManager(object):
    """
    A manager that handles the set of available course tabs.
    """

    @classmethod
    def get_tab_types(cls):
        """
        Returns the list of available tab types.
        """
        if not hasattr(cls, "_tab_types"):
            tab_types = {
                'courseware': CoursewareTab,
                'course_info': CourseInfoTab,
                'wiki': WikiTab,
                'discussion': DiscussionTab,
                'external_discussion': ExternalDiscussionTab,
                'external_link': ExternalLinkTab,
                'textbooks': TextbookTabs,
                'pdf_textbooks': PDFTextbookTabs,
                'html_textbooks': HtmlTextbookTabs,
                'progress': ProgressTab,
                'static_tab': StaticTab,
                'peer_grading': PeerGradingTab,
                'staff_grading': StaffGradingTab,
                'open_ended': OpenEndedGradingTab,
                'notes': NotesTab,
                'syllabus': SyllabusTab,
            }

            # Add any registered course views
            # TODO: don't import openedx capabilities from common
            from openedx.core.lib.plugins.api import CourseViewTypeManager
            for course_view_type in CourseViewTypeManager.get_available_plugins().values():
                tab_types[course_view_type.name] = course_view_type

            cls._tab_types = tab_types
        return cls._tab_types


class AuthenticatedCourseTab(CourseTab):
    """
    Abstract class for tabs that can be accessed by only authenticated users.
    """
    def is_enabled(self, course, settings, user=None):
        return not user or user.is_authenticated()


class StaffTab(AuthenticatedCourseTab):
    """
    Abstract class for tabs that can be accessed by only users with staff access.
    """
    def is_enabled(self, course, settings, user=None):  # pylint: disable=unused-argument
        return not user or is_user_staff(course, user)


def is_user_staff(course, user):
    """
    Returns true if the user is staff in the specified course, or globally.
    """
    from courseware.access import has_access  # pylint: disable=import-error
    return has_access(user, 'staff', course, course.id)


def is_user_enrolled_or_staff(course, user):
    """
    Returns true if the user is enrolled in the specified course,
    or if the user is staff.
    """
    from student.models import CourseEnrollment  # pylint: disable=import-error
    return is_user_staff(course, user) or CourseEnrollment.is_enrolled(user, course.id)


class EnrolledOrStaffTab(AuthenticatedCourseTab):
    """
    Abstract class for tabs that can be accessed by only users with staff access
    or users enrolled in the course.
    """
    def is_enabled(self, course, settings, user=None):  # pylint: disable=unused-argument
        if not user:
            return True
        return is_user_enrolled_or_staff(course, user)


class HideableTab(CourseTab):
    """
    Abstract class for tabs that are hideable
    """
    is_hideable = True

    def __init__(self, name, tab_id, link_func, tab_dict):
        super(HideableTab, self).__init__(
            name=name,
            tab_id=tab_id,
            link_func=link_func,
        )
        self.is_hidden = tab_dict.get('is_hidden', False) if tab_dict else False

    def __getitem__(self, key):
        if key == 'is_hidden':
            return self.is_hidden
        else:
            return super(HideableTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'is_hidden':
            self.is_hidden = value
        else:
            super(HideableTab, self).__setitem__(key, value)

    def to_json(self):
        to_json_val = super(HideableTab, self).to_json()
        if self.is_hidden:
            to_json_val.update({'is_hidden': True})
        return to_json_val

    def __eq__(self, other):
        if not super(HideableTab, self).__eq__(other):
            return False
        return self.is_hidden == other.get('is_hidden', False)


class CoursewareTab(EnrolledOrStaffTab):
    """
    A tab containing the course content.
    """

    type = 'courseware'
    is_movable = False

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(CoursewareTab, self).__init__(
            # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
            name=_('Courseware'),  # support fixed name for the courseware tab
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class CourseInfoTab(CourseTab):
    """
    A tab containing information about the course.
    """

    type = 'course_info'
    is_movable = False

    def __init__(self, tab_dict=None):
        super(CourseInfoTab, self).__init__(
            # Translators: "Course Info" is the name of the course's information and updates page
            name=tab_dict['name'] if tab_dict else _('Course Info'),
            tab_id='info',
            link_func=link_reverse_func('info'),
        )

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(CourseInfoTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class ProgressTab(EnrolledOrStaffTab):
    """
    A tab containing information about the authenticated user's progress.
    """

    type = 'progress'

    def __init__(self, tab_dict=None):
        super(ProgressTab, self).__init__(
            # Translators: "Progress" is the name of the student's course progress page
            name=tab_dict['name'] if tab_dict else _('Progress'),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )

    def is_enabled(self, course, settings, user=None):
        super_can_display = super(ProgressTab, self).is_enabled(course, settings, user=user)
        return super_can_display and not course.hide_progress_tab

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(ProgressTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class WikiTab(HideableTab):
    """
    A tab_dict containing the course wiki.
    """

    type = 'wiki'

    def __init__(self, tab_dict=None):
        super(WikiTab, self).__init__(
            # Translators: "Wiki" is the name of the course's wiki page
            name=tab_dict['name'] if tab_dict else _('Wiki'),
            tab_id=self.type,
            link_func=link_reverse_func('course_wiki'),
            tab_dict=tab_dict,
        )

    def is_enabled(self, course, settings, user=None):
        if not settings.WIKI_ENABLED:
            return False
        if not user or course.allow_public_wiki_access:
            return True
        return is_user_enrolled_or_staff(course, user)

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(WikiTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class DiscussionTab(EnrolledOrStaffTab):
    """
    A tab only for the new Berkeley discussion forums.
    """

    type = 'discussion'

    def __init__(self, tab_dict=None):
        super(DiscussionTab, self).__init__(
            # Translators: "Discussion" is the title of the course forum page
            name=tab_dict['name'] if tab_dict else _('Discussion'),
            tab_id=self.type,
            link_func=link_reverse_func('django_comment_client.forum.views.forum_form_discussion'),
        )

    def is_enabled(self, course, settings, user=None):
        if settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
            from ccx.overrides import get_current_ccx  # pylint: disable=import-error
            if get_current_ccx():
                return False
        super_can_display = super(DiscussionTab, self).is_enabled(course, settings, user=user)
        return settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE') and super_can_display

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(DiscussionTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class LinkTab(CourseTab):
    """
    Abstract class for tabs that contain external links.
    """
    link_value = ''

    def __init__(self, name, tab_id, link_value):
        self.link_value = link_value
        super(LinkTab, self).__init__(
            name=name,
            tab_id=tab_id,
            link_func=link_value_func(self.link_value),
        )

    def __getitem__(self, key):
        if key == 'link':
            return self.link_value
        else:
            return super(LinkTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'link':
            self.link_value = value
        else:
            super(LinkTab, self).__setitem__(key, value)

    def to_json(self):
        to_json_val = super(LinkTab, self).to_json()
        to_json_val.update({'link': self.link_value})
        return to_json_val

    def __eq__(self, other):
        if not super(LinkTab, self).__eq__(other):
            return False
        return self.link_value == other.get('link')

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(LinkTab, cls).validate(tab_dict, raise_error) and key_checker(['link'])(tab_dict, raise_error)


class ExternalDiscussionTab(LinkTab):
    """
    A tab that links to an external discussion service.
    """

    type = 'external_discussion'

    def __init__(self, tab_dict=None, link_value=None):
        super(ExternalDiscussionTab, self).__init__(
            # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
            name=_('Discussion'),
            tab_id='discussion',
            link_value=tab_dict['link'] if tab_dict else link_value,
        )


class ExternalLinkTab(LinkTab):
    """
    A tab containing an external link.
    """
    type = 'external_link'

    def __init__(self, tab_dict):
        super(ExternalLinkTab, self).__init__(
            name=tab_dict['name'],
            tab_id=None,  # External links are never active.
            link_value=tab_dict['link'],
        )


class StaticTab(CourseTab):
    """
    A custom tab.
    """
    type = 'static_tab'

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(StaticTab, cls).validate(tab_dict, raise_error) and key_checker(['name', 'url_slug'])(tab_dict, raise_error)

    def __init__(self, tab_dict=None, name=None, url_slug=None):
        self.url_slug = tab_dict['url_slug'] if tab_dict else url_slug
        super(StaticTab, self).__init__(
            name=tab_dict['name'] if tab_dict else name,
            tab_id='static_tab_{0}'.format(self.url_slug),
            link_func=lambda course, reverse_func: reverse_func(self.type, args=[course.id.to_deprecated_string(), self.url_slug]),
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
        to_json_val = super(StaticTab, self).to_json()
        to_json_val.update({'url_slug': self.url_slug})
        return to_json_val

    def __eq__(self, other):
        if not super(StaticTab, self).__eq__(other):
            return False
        return self.url_slug == other.get('url_slug')


class SingleTextbookTab(CourseTab):
    """
    A tab representing a single textbook.  It is created temporarily when enumerating all textbooks within a
    Textbook collection tab.  It should not be serialized or persisted.
    """
    type = 'single_textbook'
    is_movable = False
    is_collection_item = True

    def to_json(self):
        raise NotImplementedError('SingleTextbookTab should not be serialized.')


class TextbookTabsBase(AuthenticatedCourseTab):
    """
    Abstract class for textbook collection tabs classes.
    """
    is_collection = True

    def __init__(self, tab_id):
        # Translators: 'Textbooks' refers to the tab in the course that leads to the course' textbooks
        super(TextbookTabsBase, self).__init__(
            name=_("Textbooks"),
            tab_id=tab_id,
            link_func=None,
        )

    @abstractmethod
    def items(self, course):
        """
        A generator for iterating through all the SingleTextbookTab book objects associated with this
        collection of textbooks.
        """
        pass


class TextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all textbook tabs.
    """
    type = 'textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(TextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def is_enabled(self, course, settings, user=None):
        return settings.FEATURES.get('ENABLE_TEXTBOOK')

    def items(self, course):
        for index, textbook in enumerate(course.textbooks):
            yield SingleTextbookTab(
                name=textbook.title,
                tab_id='textbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class PDFTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all PDF textbook tabs.
    """
    type = 'pdf_textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(PDFTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.pdf_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='pdftextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'pdf_book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class HtmlTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all Html textbook tabs.
    """
    type = 'html_textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(HtmlTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.html_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='htmltextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'html_book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class GradingTab(object):
    """
    Abstract class for tabs that involve Grading.
    """
    pass


class StaffGradingTab(StaffTab, GradingTab):
    """
    A tab for staff grading.
    """
    type = 'staff_grading'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(StaffGradingTab, self).__init__(
            # Translators: "Staff grading" appears on a tab that allows
            # staff to view open-ended problems that require staff grading
            name=_("Staff grading"),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class PeerGradingTab(AuthenticatedCourseTab, GradingTab):
    """
    A tab for peer grading.
    """
    type = 'peer_grading'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(PeerGradingTab, self).__init__(
            # Translators: "Peer grading" appears on a tab that allows
            # students to view open-ended problems that require grading
            name=_("Peer grading"),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class OpenEndedGradingTab(AuthenticatedCourseTab, GradingTab):
    """
    A tab for open ended grading.
    """
    type = 'open_ended'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(OpenEndedGradingTab, self).__init__(
            # Translators: "Open Ended Panel" appears on a tab that, when clicked, opens up a panel that
            # displays information about open-ended problems that a user has submitted or needs to grade
            name=_("Open Ended Panel"),
            tab_id=self.type,
            link_func=link_reverse_func('open_ended_notifications'),
        )


class SyllabusTab(CourseTab):
    """
    A tab for the course syllabus.
    """
    type = 'syllabus'

    def is_enabled(self, course, settings, user=None):
        return hasattr(course, 'syllabus_present') and course.syllabus_present

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(SyllabusTab, self).__init__(
            # Translators: "Syllabus" appears on a tab that, when clicked, opens the syllabus of the course.
            name=_('Syllabus'),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class NotesTab(AuthenticatedCourseTab):
    """
    A tab for the course notes.
    """
    type = 'notes'

    def is_enabled(self, course, settings, user=None):
        return settings.FEATURES.get('ENABLE_STUDENT_NOTES')

    def __init__(self, tab_dict=None):
        super(NotesTab, self).__init__(
            name=tab_dict['name'],
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(NotesTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class CourseViewTab(AuthenticatedCourseTab):
    """
    A tab that renders a course view.
    """

    def __init__(self, course_view_type, tab_dict=None):
        super(CourseViewTab, self).__init__(
            name=tab_dict['name'] if tab_dict else course_view_type.title,
            tab_id=course_view_type.name,
            link_func=link_reverse_func(course_view_type.view_name),
        )
        self.type = course_view_type.name
        self.course_view_type = course_view_type

    def is_enabled(self, course, settings, user=None):
        if not super(CourseViewTab, self).is_enabled(course, settings, user=user):
            return False
        return self.course_view_type.is_enabled(course, settings, user=user)


class CourseTabList(List):
    """
    An XBlock field class that encapsulates a collection of Tabs in a course.
    It is automatically created and can be retrieved through a CourseDescriptor object: course.tabs
    """

    @staticmethod
    def initialize_default(course):
        """
        An explicit initialize method is used to set the default values, rather than implementing an
        __init__ method.  This is because the default values are dependent on other information from
        within the course.
        """

        course.tabs.extend([
            CoursewareTab(),
            CourseInfoTab(),
        ])

        # Presence of syllabus tab is indicated by a course attribute
        if hasattr(course, 'syllabus_present') and course.syllabus_present:
            course.tabs.append(SyllabusTab())

        # If the course has a discussion link specified, use that even if we feature
        # flag discussions off. Disabling that is mostly a server safety feature
        # at this point, and we don't need to worry about external sites.
        if course.discussion_link:
            discussion_tab = ExternalDiscussionTab(link_value=course.discussion_link)
        else:
            discussion_tab = DiscussionTab()

        course.tabs.extend([
            TextbookTabs(),
            discussion_tab,
            WikiTab(),
            ProgressTab(),
        ])

    @staticmethod
    def get_discussion(course):
        """
        Returns the discussion tab for the given course.  It can be either of type DiscussionTab
        or ExternalDiscussionTab.  The returned tab object is self-aware of the 'link' that it corresponds to.
        """

        # the discussion_link setting overrides everything else, even if there is a discussion tab in the course tabs
        if course.discussion_link:
            return ExternalDiscussionTab(link_value=course.discussion_link)

        # find one of the discussion tab types in the course tabs
        for tab in course.tabs:
            if isinstance(tab, DiscussionTab) or isinstance(tab, ExternalDiscussionTab):
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
    def iterate_displayable(course, settings, user=None, inline_collections=True):
        """
        Generator method for iterating through all tabs that can be displayed for the given course and
        the given user with the provided access settings.
        """
        for tab in course.tabs:
            if tab.is_enabled(course, settings, user=user) and (not user or not tab.is_hideable or not tab.is_hidden):
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

        if tabs[0].get('type') != CoursewareTab.type:
            raise InvalidTabsException(
                "Expected first tab to have type 'courseware'.  tabs: '{0}'".format(tabs))

        if tabs[1].get('type') != CourseInfoTab.type:
            raise InvalidTabsException(
                "Expected second tab to have type 'course_info'.  tabs: '{0}'".format(tabs))

        # the following tabs should appear only once
        for tab_type in [
                CoursewareTab.type,
                CourseInfoTab.type,
                NotesTab.type,
                TextbookTabs.type,
                PDFTextbookTabs.type,
                HtmlTextbookTabs.type,
                CourseViewTab.type
        ]:
            cls._validate_num_tabs_of_type(tabs, tab_type, 1)

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
        self.validate_tabs(values)
        return [CourseTab.from_json(tab_dict) for tab_dict in values]


#### Link Functions
def link_reverse_func(reverse_name):
    """
    Returns a function that takes in a course and reverse_url_func,
    and calls the reverse_url_func with the given reverse_name and course' ID.
    """
    return lambda course, reverse_url_func: reverse_url_func(reverse_name, args=[course.id.to_deprecated_string()])


def link_value_func(value):
    """
    Returns a function takes in a course and reverse_url_func, and returns the given value.
    """
    return lambda course, reverse_url_func: value


#### Validators
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
