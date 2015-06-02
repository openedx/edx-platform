"""
This module is essentially a broker to xmodule/tabs.py -- it was originally introduced to
perform some LMS-specific tab display gymnastics for the Entrance Exams feature
"""
from django.conf import settings
from django.utils.translation import ugettext as _

from courseware.access import has_access
from courseware.entrance_exams import user_must_complete_entrance_exam
from openedx.core.djangoapps.course_views.course_views import CourseViewTypeManager, CourseViewType, StaticTab
from student.models import CourseEnrollment
from xmodule.tabs import CourseTab, CourseTabList, key_checker


class EnrolledCourseViewType(CourseViewType):
    """
    A base class for any view types that require a user to be enrolled.
    """
    @classmethod
    def is_enabled(cls, course, user=None):
        if user is None:
            return True
        return CourseEnrollment.is_enrolled(user, course.id) or has_access(user, 'staff', course, course.id)


class CoursewareViewType(EnrolledCourseViewType):
    """
    The main courseware view.
    """
    name = 'courseware'
    title = _('Courseware')
    priority = 10
    view_name = 'courseware'
    is_movable = False


class CourseInfoViewType(CourseViewType):
    """
    The course info view.
    """
    name = 'course_info'
    title = _('Course Info')
    priority = 20
    view_name = 'info'
    tab_id = 'info'
    is_movable = False

    @classmethod
    def is_enabled(cls, course, user=None):
        return True


class SyllabusCourseViewType(EnrolledCourseViewType):
    """
    A tab for the course syllabus.
    """
    name = 'syllabus'
    title = _('Syllabus')
    priority = 30
    view_name = 'syllabus'

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        if not super(SyllabusCourseViewType, cls).is_enabled(course, user=user):
            return False
        return getattr(course, 'syllabus_present', False)


class ProgressCourseViewType(EnrolledCourseViewType):
    """
    The course progress view.
    """
    name = 'progress'
    title = _('Progress')
    priority = 40
    view_name = 'progress'
    is_hideable = True

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        if not super(ProgressCourseViewType, cls).is_enabled(course, user=user):
            return False
        return not course.hide_progress_tab


class TextbookCourseViewsBase(CourseViewType):
    """
    Abstract class for textbook collection tabs classes.
    """
    # Translators: 'Textbooks' refers to the tab in the course that leads to the course' textbooks
    title = _("Textbooks")
    is_collection = True

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        return user is None or user.is_authenticated()

    @classmethod
    def items(cls, course):
        """
        A generator for iterating through all the SingleTextbookTab book objects associated with this
        collection of textbooks.
        """
        raise NotImplementedError()


class TextbookCourseViews(TextbookCourseViewsBase):
    """
    A tab representing the collection of all textbook tabs.
    """
    name = 'textbooks'
    priority = None
    view_name = 'book'

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        parent_is_enabled = super(TextbookCourseViews, cls).is_enabled(course, user)
        return settings.FEATURES.get('ENABLE_TEXTBOOK') and parent_is_enabled

    @classmethod
    def items(cls, course):
        for index, textbook in enumerate(course.textbooks):
            yield SingleTextbookTab(
                name=textbook.title,
                tab_id='textbook/{0}'.format(index),
                view_name=cls.view_name,
                index=index
            )


class PDFTextbookCourseViews(TextbookCourseViewsBase):
    """
    A tab representing the collection of all PDF textbook tabs.
    """
    name = 'pdf_textbooks'
    priority = None
    view_name = 'pdf_book'

    @classmethod
    def items(cls, course):
        for index, textbook in enumerate(course.pdf_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='pdftextbook/{0}'.format(index),
                view_name=cls.view_name,
                index=index
            )


class HtmlTextbookCourseViews(TextbookCourseViewsBase):
    """
    A tab representing the collection of all Html textbook tabs.
    """
    name = 'html_textbooks'
    priority = None
    view_name = 'html_book'

    @classmethod
    def items(cls, course):
        for index, textbook in enumerate(course.html_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='htmltextbook/{0}'.format(index),
                view_name=cls.view_name,
                index=index
            )


class StaticCourseViewType(CourseViewType):
    """
    The view type that shows a static tab.
    """
    name = 'static_tab'
    is_default = False    # A static tab is never added to a course by default
    allow_multiple = True

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        """
        Static tabs are viewable to everyone, even anonymous users.
        """
        return True

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Ensures that the specified tab_dict is valid.
        """
        return (super(StaticCourseViewType, cls).validate(tab_dict, raise_error)
                and key_checker(['name', 'url_slug'])(tab_dict, raise_error))

    @classmethod
    def create_tab(cls, tab_dict):
        """
        Returns the tab that will be shown to represent an instance of a view.
        """
        return StaticTab(tab_dict)


class ExternalDiscussionCourseViewType(EnrolledCourseViewType):
    """
    A course view links to an external discussion service.
    """

    name = 'external_discussion'
    # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
    title = _('Discussion')
    priority = None

    @classmethod
    def create_tab(cls, tab_dict):
        """
        Returns the tab that will be shown to represent an instance of a view.
        """
        return LinkTab(tab_dict, cls.title)

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """ Validate that the tab_dict for this course view has the necessary information to render. """
        return (super(ExternalDiscussionCourseViewType, cls).validate(tab_dict, raise_error) and
                key_checker(['link'])(tab_dict, raise_error))

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        if not super(ExternalDiscussionCourseViewType, cls).is_enabled(course, user=user):
            return False
        return course.discussion_link


class ExternalLinkCourseViewType(EnrolledCourseViewType):
    """
    A course view containing an external link.
    """
    name = 'external_link'
    priority = None
    is_default = False    # An external link tab is not added to a course by default

    @classmethod
    def create_tab(cls, tab_dict):
        """
        Returns the tab that will be shown to represent an instance of a view.
        """
        return LinkTab(tab_dict)

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """ Validate that the tab_dict for this course view has the necessary information to render. """
        return (super(ExternalLinkCourseViewType, cls).validate(tab_dict, raise_error) and
                key_checker(['link', 'name'])(tab_dict, raise_error))


class LinkTab(CourseTab):
    """
    Abstract class for tabs that contain external links.
    """
    link_value = ''

    def __init__(self, tab_dict=None, name=None, link=None):
        self.link_value = tab_dict['link'] if tab_dict else link

        def link_value_func(_course, _reverse_func):
            """ Returns the link_value as the link. """
            return self.link_value

        self.type = tab_dict['type']

        super(LinkTab, self).__init__(
            name=tab_dict['name'] if tab_dict else name,
            tab_id=None,
            link_func=link_value_func,
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


class SingleTextbookTab(CourseTab):
    """
    A tab representing a single textbook.  It is created temporarily when enumerating all textbooks within a
    Textbook collection tab.  It should not be serialized or persisted.
    """
    type = 'single_textbook'
    is_movable = False
    is_collection_item = True
    priority = None

    def __init__(self, name, tab_id, view_name, index):
        def link_func(course, reverse_func, index=index):
            """ Constructs a link for textbooks from a view name, a course, and an index. """
            return reverse_func(view_name, args=[unicode(course.id), index])

        super(SingleTextbookTab, self).__init__(name, tab_id, link_func)

    def to_json(self):
        raise NotImplementedError('SingleTextbookTab should not be serialized.')


def get_course_tab_list(request, course):
    """
    Retrieves the course tab list from xmodule.tabs and manipulates the set as necessary
    """
    user = request.user
    xmodule_tab_list = CourseTabList.iterate_displayable(course, user=user)

    # Now that we've loaded the tabs for this course, perform the Entrance Exam work.
    # If the user has to take an entrance exam, we'll need to hide away all but the
    # "Courseware" tab. The tab is then renamed as "Entrance Exam".
    course_tab_list = []
    for tab in xmodule_tab_list:
        if user_must_complete_entrance_exam(request, user, course):
            # Hide all of the tabs except for 'Courseware'
            # Rename 'Courseware' tab to 'Entrance Exam'
            if tab.type is not 'courseware':
                continue
            tab.name = _("Entrance Exam")
        course_tab_list.append(tab)

    # Add in any dynamic tabs, i.e. those that are not persisted
    course_tab_list += _get_dynamic_tabs(course, user)
    return course_tab_list


def _get_dynamic_tabs(course, user):
    """
    Returns the dynamic tab types for the current user.

    Note: dynamic tabs are those that are not persisted in the course, but are
    instead added dynamically based upon the user's role.
    """
    dynamic_tabs = list()
    for tab_type in CourseViewTypeManager.get_course_view_types():
        if getattr(tab_type, "is_dynamic", False):
            tab = tab_type.create_tab(dict())
            if tab.is_enabled(course, user=user):
                dynamic_tabs.append(tab)
    dynamic_tabs.sort(key=lambda dynamic_tab: dynamic_tab.name)
    return dynamic_tabs
